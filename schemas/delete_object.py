import time
import pandas as pd
import pathlib
from schemas import tm_services as sv
from schemas.mongo_schema import MongoManager
from utilities.workbook import WorkbookFormats
from schemas.fields import UserModel, Status, Priority
from devtools import debug

task_db = MongoManager('Task')
db = task_db.get_db()

cursor = db.tasks.update_many(
    {},
    {'$unset': {'user_name': ''}}
)
quit()

cursor = db.tasks.find(
    {},
)

records = []
for c in cursor:
    db.tasks.update_one(
        {'_id': c.get('_id')},
        {
            '$set': {
                'full_name': c.get('user_name').get('user_object').get('full_name')
            }
        }
    )
quit()


# dff = pd.DataFrame(pd.DataFrame(task_db.get_collection(collection='tasks')))


