import re
import subprocess
import codecs
import json
import string
import logging.config
import yaml
import functools
import pathlib
import time
import pymongo.cursor
import pandas as pd
import certifi
from datetime        import datetime
from pymongo         import MongoClient
from bson.objectid   import ObjectId
from typing          import List, Dict
from pydantic        import ValidationError
from pymongo         import results
from typing          import Any
from schemas.fields  import TaskUpdateModel
from schemas.fields  import  Department, Status, Priority, Source, WMSDomain
from devtools        import debug

###########################################
today = datetime.today()
dt_date = datetime.now()
dt_date = pd.to_datetime(dt_date - pd.DateOffset(months=1)) + pd.offsets.MonthEnd()
dt_date = dt_date.strftime('%Y-%m-%d')

root      = pathlib.Path(__file__).parent.parent
data_path = root.joinpath('resources', 'data')
conf_path = root.joinpath('resources')
CONF_FILE = root.joinpath(conf_path, 'config.yaml' ).as_posix()
LOG_FILE  = root.joinpath(conf_path, 'logging.yaml').as_posix()
PAGE_SIZE = 9
o_category  = ['username', 'department', 'status', 'priority', 'source', 'wms_domain']

with codecs.open(LOG_FILE, 'r', encoding='utf-8') as f:
    log_config = yaml.safe_load(f)

with open(LOG_FILE, 'r') as f:
    config = yaml.safe_load(f.read())
    logging.config.dictConfig(config)
logger = logging.getLogger(__name__)

def log_decorator(func):
    @functools.wraps(func)
    def log_decorator_wrapper(*args, **kwargs):
        args_passed = [repr(a) for a in args]
        kwargs_pass = ['{}={!r}'.format(k, v) for k, v in kwargs.items()]
        format_args = ', '.join(args_passed + kwargs_pass)
        logger.debug('{}: begin function'.format(func.__name__))
        value = func(*args,**kwargs)
        logger.debug('{}: ended'.format(func.__name__))
        return value
    return log_decorator_wrapper

def timing_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logger.info(f" {func.__name__:>25} took {end_time - start_time:.5f} seconds")
        return result
    return wrapper

class MongoManager:
    def __init__(self, db):
        self._db_name = db
        self._db = self.connect()
        self._digs = string.digits + string.ascii_letters
        self._client = None

    @staticmethod
    def ping_test(host: str) -> None:
        result = subprocess.call('ping os -n 2' % host)
        if result ==0:
            logger.info('{}: success'. format(host))
        else:
            logger.critical('{}: failed'. format (host))
            quit(-1)

    @staticmethod
    def get_logger():
        return logger

    def connect(self):
        logger.info ('MongoDB : Start Connection...')
        self._client = MongoClient ('mongodb://127.0.0.1:27017/', serverSelectionTimeoutMS=1000)
        moshe = self._client["Task"].list_collections()
        moshe = [c for c in moshe]
        print(f'\tnumber of collections: {len(moshe)}')
        _db = self._client[self._db_name]
        cursor = _db['tasks'].count_documents({})
        print(f'\tcollection tasks has {cursor} documents')
        return _db

    def get_db(self):
        return self._db

    @staticmethod
    def parse_object_id(oid: str):
        ts = ObjectId(oid).generation_time.strftime('%Y-%m-%d')
        serial = int(oid[-4:], base=16)
        moshe = [oid, serial, ts]
        return moshe

    ####################################################################################################################

    def get_document_by_oid(self, collection: str, oid: str) -> pymongo.cursor.Cursor:
        db = self._db
        cursor = db[collection].find_one_and_update(
            {'_id': ObjectId(oid)},
            {
                '$set': {
                    'myLock': {
                        'appName'     : 'tm_app',
                        'pseudoRandom': ObjectId()
                    }
                }
            }
        )
        # moshe = [c for c in cursor]
        return cursor

    def get_document_by_oid_old(self, collection: str, oid: str) -> pymongo.cursor.Cursor:
        db = self._db
        cursor = db[collection].find(
            {'_id': ObjectId(oid)}
        )
        return cursor

    def get_document_by_field(self, collection: str, field: str, value: str) -> pymongo.cursor.Cursor:
        db = self._db
        cursor = db[collection].find(
            {field: value}
        )
        return cursor

    def get_documents_by_query(self, collection: str, query: dict):
        db = self._db
        cursor = db[collection].find(query)
        return cursor

    @log_decorator
    def db_update_by_query(self, collection: str, query: dict) -> Any:
        logger.info('updated record')
        logger.info(json.dumps(query))
        db = self._db
        return db[collection].update_many(query)

    def insert_one_document(self, collection, record):
        db = self._db
        cursor = db[collection].insert_one(record)
        return cursor

    def insert_many_documents(self, collection: str, documents: List) -> Any:
        db = self._db
        cursor = db[collection].insert_many(documents=documents)
        return cursor

    def delete_one(self, collection: str, query: dict) -> results.DeleteResult:
        db = self._db
        cursor = db[collection].delete_one(query)
        return cursor

    @log_decorator
    def update_document_by_oid(self, collection: str, document: dict, oid: str):
        db = self._db
        logger.info('updated record')
        json_string = json.dumps(document, indent=4, ensure_ascii=False).encode('utf-8').decode()
        logger.info(oid + ': ' + json_string)
        cursor = db[collection].update_one(
            {'_id' : ObjectId(oid)},
            {'$set': document}
        )
        return cursor

    def update_field_by_oid(self, collection: str, query: dict, oid: str):
        db = self._db
        cursor = db[collection].update_one(
            {'_id' : ObjectId(oid)},
            {'$set': query}
        )
        success = True if cursor.matched_count > 0 else False
        if not success:
            logger.info('update failed')
            json_string = json.dumps(query, indent=4, ensure_ascii=False).encode('utf-8').decode()
            logger.info(oid + ': ' + json_string)
            quit()
        return success

    def update_many_by_matched_value(self, collection: str, field: str, value: str, new_value: str) -> bool:
        db = self._db
        cursor = db[collection].update_many(
            {field: value},
            {
                '$set': {
                    field: new_value
                }
            }
        )
        logger.info('match: {} modified: {}'.format(cursor.matched_count,cursor.modified_count))
        return cursor.acknowledged

    def update_one_by_field_value(self, collection: str, oid: str, field: str, new_value: str) -> bool:
        db = self._db
        cursor = db[collection].update_one(
            {'_id': ObjectId(oid) },
            {
                '$set': {
                    field: new_value
                }
            }
        )
        return cursor.acknowledged

    def update_one_by_query(self, collection: str, query: set) -> Any:
        db = self._db
        cursor = db[collection].update_one(query)
        return cursor

    def get_unique_value(self, collection: str, field_name: str):
        db = self._db
        return db[collection].distinct(field_name)

    def find_documents_by_query(self, collection: str, query) -> List:
        db = self._db
        data = []
        db_collection = db[collection]
        cursor = db_collection.find(query)
        [data.append(c) for c in cursor]
        return data

    @log_decorator
    def update_task_document(self, u_data: dict):
        def value_from_validation_error(d: Dict, error: ValidationError):
            for error in error.errors():
                loc = list(error["loc"])[0]
                msg = error['msg']
                return f'{loc} {msg}'

        db = self._db
        try:
            TaskUpdateModel.parse_obj(u_data)
        except ValidationError as ex:
            msg = value_from_validation_error(d=u_data, error=ex)
            return msg

        owner_note = u_data.pop('owner_note')
        user_name  = u_data.pop('user_name' )
        row_id     = u_data.pop('row_id'    )
        user_role  = u_data.pop('role'      )
        owner_name = u_data.pop('owner_name')
        sheet      = u_data.pop('sheet'     )

        update_query = {}
        for key, value in u_data.items():
            if value:
                update_query.update({key: value})

        if bool(update_query):
            for key, value in update_query.items():
                if key == 'due_date':
                    update_query[key] = pd.to_datetime(value, format='%d/%m/%Y').strftime('%Y-%m-%d')
                    break

        ##############################################################################################
        update_query.update(
            {
                'update.user'    : user_name,
                'reference.sheet': sheet  # this is any reference user have such as QC number
            }
        )
        ##############################################################################################
        cursor = db.tasks.update_one(
            {'_id': ObjectId(row_id)},
            {
                '$push': {
                    'owner_notes':
                        {
                            'note_id'  : ObjectId(),
                            'note'     : owner_note,
                            'note_date': datetime.now().strftime('%d/%m/%Y')
                        },
                    'audit':
                        {
                            'when': datetime.now(),
                            'what': update_query
                        }
                },
                '$set'        : update_query,
                '$currentDate': {'update.lastUpdated': True},
            }
        )
        result = cursor.raw_result.get('updatedExisting')
        return result

    @staticmethod
    def _refresh_data(task_records: List) -> pd.DataFrame:
        df = pd.DataFrame(task_records)
        if len(df) == 0:
            return df

        df.rename(
            columns={
                'telephone': 'tn',
                'full_name': 'u_name'
            },
            inplace=True
        )
        df['source'        ] = [s.get('source'     ) for s in df['reference' ]]
        df['sheet'         ] = [s.get('sheet'      ) for s in df['reference' ]]
        df['doctype'       ] = [s.get('doctype'    ) for s in df['reference' ]]
        df['wms_domain'    ] = [s.get('domain'     ) for s in df['wms_object']]
        df['w_process'     ] = [s.get('process'    ) for s in df['wms_object']]
        df['w_sub_process' ] = [s.get('sub_process') for s in df['wms_object']]

        df.drop(['reference'], axis=1, inplace=True)

        df_table = pd.DataFrame()
        try:
            df_table = df[[
                '_id', 'source', 'sheet', 'row_number', 'wms_domain', 'w_process', 'w_sub_process', 'doctype',
                'sap_domain', 'sap_process', 'priority',
                'subject', 'status',
                'u_name', 'department', 'tn', 'email', 'role',
                'start', 'finish', 'due_date',
                # 'note', 'owner_notes'
            ]]
        except KeyError as ex:
            print('u_name key error in _refresh_data', ex)
        df_table = df_table.copy()

        df_table['id'] = df_table.index
        df_table['_id'] = [str(x) for x in df_table['_id']]
        return df_table

    @staticmethod
    def _tasks_filter_parser(grand_filter: Dict) -> (Dict, Dict):
        search = grand_filter.pop("search")
        d1 = '\"'
        if search is None:
            search_query = None
        elif search.isdigit():
            search_query = {'row_number': int(search)}
        elif ObjectId.is_valid(search):
            search_query = {'_id': ObjectId(search)}
        else:
            moshe = len(search)
            if moshe > 0:
                # search = f'"\"{search}\""'
                search = f'{d1}{search}{d1}'
                print(f'->{search}<-')
                search_query = {'$text': {'$search': search}}
            else:
                search_query = None

        ##########
        ##########
        ##########
        ##########
        ##########
        ##########
        ##########
        # search_query = {'$text': {'$search': 'T_01'}}
        ##########
        ##########
        ##########
        ##########
        ##########

        updated_query = {}
        for key, value in grand_filter.items():
            if value:
                updated_query.update({key: value})

        return search_query, updated_query

    def grand_filter_query(self, collection: str, grand_filter: dict, skip: int) -> pd.DataFrame:
        db = self._db
        department = grand_filter.pop('department')

        search_query, updated_query = self._tasks_filter_parser(grand_filter)
        cursor = db[collection].aggregate(
            [
                {
                    '$match': {
                            '$and': [
                                {} if search_query is None else search_query,
                                updated_query
                            ]
                        }
                },
                {
                    '$lookup': {
                        'from'        : 'user',
                        'localField'  : 'full_name',
                        'foreignField': 'full_name',
                        'as'          : 'user_object'
                    }
                },
                {
                    '$replaceRoot': {
                        'newRoot': {
                            '$mergeObjects': [
                                {
                                    '$arrayElemAt': ["$user_object", 0]
                                },
                                "$$ROOT"
                            ]
                        }
                    }
                },
                {
                    '$project': {
                        'user_object': 0,
                    }
                },
                {
                    '$match': {
                        'department': {'$regex': re.compile(r"[*]*")}  if department is None else department
                    }
                },
                {
                    '$facet': {
                        'records': [
                            {'$skip' : PAGE_SIZE * skip},
                            {'$limit': PAGE_SIZE}
                        ],
                        'records_count': [
                            {'$count': 'documents'}
                        ],
                    }
                },
            ]
        )
        facet_results = [c for c in cursor][0]
        records       = facet_results.get('records')
        documents     = facet_results.get('records_count')[0].get('documents')

        return (self._refresh_data(task_records=records), documents) if records else (pd.DataFrame, 0)

    def multi_facet_query(self, collection: str, grand_filter: Dict):
        # moshe = self.multi_facet_query_x(collection=collection, grand_filter=grand_filter)
        db = self._db
        department = grand_filter.pop('department')
        search_query, updated_query = self._tasks_filter_parser(grand_filter=grand_filter)
        cursor = db[collection].aggregate(
            [
                {
                    '$match': {
                        '$and': [
                            {} if search_query is None else search_query,
                            updated_query
                        ]
                    }
                },
                {
                    '$lookup': {
                        'from'        : 'user',
                        'localField'  : 'full_name',
                        'foreignField': 'full_name',
                        'as'          : 'user_object'
                    }
                },
                {
                    '$replaceRoot': {
                        'newRoot': {
                            '$mergeObjects': [
                                {
                                    '$arrayElemAt': ["$user_object", 0]
                                },
                                "$$ROOT"
                            ]
                        }
                    }
                },
                {
                    '$project': {
                        'user_object': 0,
                    }
                },
                {
                    '$match': {
                        'department': {'$regex': re.compile(r"[*]*")}  if department is None else department
                    }
                },
                {
                    '$facet': {
                        'group_1': [
                            {
                                '$group': {
                                    '_id': {
                                        'u_name': '$full_name',
                                        'status': '$status'
                                    },
                                    'count': {'$sum': 1}
                                }
                            }
                        ],
                        'group_2': [
                            {
                                '$match': {
                                    'due_date': {'$lt': dt_date},
                                    'status'  : 'פתוח'
                                }
                            },
                            {
                                '$group': {
                                    '_id': {
                                        'u_name': '$full_name',
                                    },
                                    'count': {'$sum': 1}
                                }
                            }
                        ],
                        'option_list': [
                            {
                                '$group': {
                                    '_id': {
                                        'username'  : '$full_name'       ,
                                        'department': '$department'      ,
                                        'status'    : '$status'          ,
                                        'priority'  : '$priority'        ,
                                        'source'    : '$reference.source',
                                        'wms_domain': '$wms_object.domain'
                                    }
                                },
                            }
                        ],
                        'records_count': [
                            {
                                '$count': 'documents'
                            }
                        ],
                        'records': [
                            {'$limit': PAGE_SIZE}
                        ]
                    }
                },
            ]
        )
        moshe = [c for c in cursor]

        o_dropdowns = []
        options = moshe[0].get('option_list')
        for opt in o_category:
            o_values = sorted(list(set([m.get('_id').get(opt) for m in options])))
            o_dropdown = [{'label': i, 'value': i} for i in o_values]
            o_dropdowns.append(o_dropdown)

        group_1 = moshe[0].get('group_1')
        records = []
        for v in group_1:
            record = {
                'u_name': v.get('_id').get('u_name'),
                'status': v.get('_id').get('status'),
                'count' : v.get('count')
            }
            records.append(record)

        df1 = pd.DataFrame(records).sort_values('u_name') if records else pd.DataFrame()

        group_2 = moshe[0].get('group_2')
        records = []
        for v in group_2:
            record = {
                'u_name': v.get('_id').get('u_name'),
                'count' : v.get('count')
            }
            records.append(record)

        df2       = pd.DataFrame(records).sort_values('u_name') if records else pd.DataFrame()
        documents = moshe[0].get('records_count')[0].get('documents') if len(df1) > 0 else 0

        records = moshe[0].get('records')
        dff = self._refresh_data(task_records=records) if records else pd.DataFrame()

        return o_dropdowns, df1, df2, documents, dff
