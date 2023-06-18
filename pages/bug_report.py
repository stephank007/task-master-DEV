import dash
import dash_bootstrap_components as dbc
import schemas.tm_services as sv
from dash import html, dcc, register_page, Input, Output, State, callback
from schemas.fields import ResetLoginModel, Department
from urllib.parse import unquote
from devtools import debug
from bson import ObjectId

task_db = sv.task_db
db = task_db.get_db()

register_page(
    __name__,
    path='/home/bug_report',
    path_template='/home/bug_report<bug_row>',
)
def get_selected_testplan_data(test_plan_oid: ObjectId):
    query = [
        {
            '$match': {
                'mtp_object.test_plan': {
                    '$elemMatch': {'test_oid': test_plan_oid}
                }
            }
        },
        {
            '$unwind': '$mtp_object.test_plan'
        },
        {
            '$match': {
                'mtp_object.test_plan.test_oid': test_plan_oid
            }
        },
        {
            '$replaceWith': '$mtp_object.test_plan'
        }
    ]
    return task_db.aggregate_query(collection='tasks', query=query)

def layout(bug_row=None, **other_unknown_query_strings):
    step_record = None
    if bug_row:
        bug_record = unquote(bug_row)
        bug_record = bug_record.replace('/', '')
        step_record = eval(bug_record)

        mtp_oid  = ObjectId(step_record.get('mtp_oid' ))
        test_oid = ObjectId(step_record.get('test_oid'))

        cursor = db.tasks.find({'mtp_object.mtp_oid': mtp_oid})
        mtp_record = [c for c in cursor][0].get('mtp_object')

        cursor = get_selected_testplan_data(test_plan_oid=test_oid)
        test_record = [c for c in cursor][0]

        debug(step_record)

    bug_report = dbc.Container(
        [
            html.Div("טופס דיווח תקלה", className="h2 p-2 text-white bg-primary text-center"),
            html.Div(f'bug_row: {step_record}')
        ],
        fluid=True
    )
    return bug_report

