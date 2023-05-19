import pandas as pd
import pathlib
from bson.objectid import ObjectId
from schemas.mongo_schema import MongoManager
import codecs
import json

ROOT_PATH     = pathlib.Path.cwd().parent
RESOURCE_PATH = ROOT_PATH.joinpath('assets')
CONF_PATH     = ROOT_PATH.joinpath('src', 'config')
DATA_PATH     = ROOT_PATH.joinpath('resources', 'data')
CONF_FILE     = CONF_PATH.joinpath('config.yaml')
AVI_PATH      = ROOT_PATH.joinpath('resources', 'data', '_in', 'PDR DB')

with open(DATA_PATH.joinpath('_in', 'avi_tasks.json'), encoding='utf-8') as f:
    json_file = json.load(f)

task_db = MongoManager('Task')
query = {'reference.secret_1': '__avi__'}
db = task_db.get_db()
db.tasks.delete_many(query)
db.tasks.insert_many(json_file)
quit()

dff = pd.read_json(json_file)
print(dff.shape)
f2 = AVI_PATH.joinpath('avi-ym.xlsx').as_posix()
f2 = AVI_PATH.joinpath('avi-ym.xlsx').as_posix()
df_tasks = pd.read_excel(f2, sheet_name='data')

task_db = MongoManager('Task')
query = {'reference.secret_1': '__nofar__'}

db = task_db.get_db()
db.tasks.delete_many(query)
quit()

for index, row in df_tasks.iterrows():
    db_id = ObjectId(row['_id'])
    record = {'_id': db_id}
    result = task_db.delete_one(collection='tasks', query=record)
    print(result.deleted_count)


