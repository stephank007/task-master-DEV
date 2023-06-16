import dash
from urllib.parse import unquote
import dash_bootstrap_components as dbc
from dash import html, dcc, register_page, Input, Output, State, callback
import schemas.tm_services as sv
from schemas.fields import ResetLoginModel, Department
from devtools import debug

task_db = sv.task_db

register_page(
    __name__,
    path='/home/bug_report',
    path_template='/home/bug_report<bug_row>',
)

def layout(bug_row=None, **other_unknown_query_strings):
    moshe = None
    if bug_row:
        moshe = unquote(bug_row)
        moshe = moshe.replace('/', '')
        moshe = eval(moshe)
        debug(moshe)

    bug_report = dbc.Container(
        [
            html.Div(f'bug_row: {moshe}')
        ],
        fluid=True
    )
    return bug_report

