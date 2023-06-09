import dash
import json
import dash_ag_grid as dag
from dash import Dash, html, dcc, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import pandas as pd
from schemas.mongo_schema import MongoManager
from schemas.fields import Status
from devtools import debug
from bson import ObjectId

clouds = '<i class="fa fa-cloud d-flex flex-row justify-content-center" style="color: grey;"></i>'
rain   = '<i class="fa fa-cloud-rain d-flex flex-row justify-content-center"></i>'
upload = '<i class="fas fa-upload d-flex flex-row justify-content-center" style="color: gold;"></i>'

task_db = MongoManager('Task')
db      = task_db.get_db()

def get_testrun_data(test_plan_oid: ObjectId):
    query = [
        {
            '$match': {
                'mtp_object.test_plan': {
                    '$elemMatch': {'test_name': 'TID_01'}
                }
            }
        },
        {
            '$unwind': '$mtp_object.test_plan'
        },
        {
            '$match': {
                'mtp_object.test_plan.test_name': 'TID_01'
            }
        },
        {
            '$replaceWith': '$mtp_object.test_plan'
        }
    ]
    return task_db.aggregate_query(collection='tasks', query=query)

df = pd.DataFrame(get_testrun_data(test_plan_oid=None)[0].get('test_steps'))

df['step_oid'] = df['step_oid'].astype(str)
df['test_oid'] = df['test_oid'].astype(str)
df['mtp_oid' ] = df['mtp_oid' ].astype(str)
df['bug'     ] = 'Bug'

app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

columnDefs = [
    {
        'headerName': "mtp_oid",
        'field': "mtp",
        'hide': True,
        'suppressToolPanel': True
    },
    {
        'headerName': "test_oid",
        'field': "test_oid",
        'hide': True,
        'suppressToolPanel': True
    },
    {
        'headerName'       : "step_oid",
        'field'            : "step_oid",
        'hide'             : True,
        'suppressToolPanel': True
    },
    {
        "headerName": "#",
        "field": "step",
        'width': 40,
        'type': 'centerAligned',
        'cellStyle': {
            'textAlign': 'center',
        }
    },
    {
        "headerName": "פעולה",
        "field": "subject",
        'width': 120,
        'cellStyle': {
            'direction'  : 'rtl',
            'white-space': 'normal',
            'word-break' : 'break-word'
        }
    },
    {
        "headerName": "תוצאה רצויה",
        "field": "expected",
        'width': 120,
        'cellStyle': {
            'textAlign': 'right',
            'direction': 'rtl',
            'white-space': 'normal',
            'word-break': 'break-word'
        }
    },
    {
        "headerName": "תוצאה שנתקבלה",
        "field": "actual_result",
        'width': 200,
        "editable": True,
        "cellEditorPopup": True,
        "cellEditor": "agLargeTextCellEditor",
        'cellStyle': {
            'textAlign': 'right',
            'direction': 'rtl',
            'white-space': 'normal',
            'word-break': 'break-word'
        }
    },
    {
        "headerName": "סטאטוס",
        "field": "status",
        'width': 75,
        "editable": True,
        "cellEditor": "agSelectCellEditor",
        "cellEditorParams": {
            "values": [Status.P_10, Status.P_11, Status.P_12, Status.P_02],
        },
    },
    {
        "headerName": "הערות",
        "field": "comments",
        'width': 200,
        "editable": True,
        "cellEditorPopup": True,
        "cellEditor": "agLargeTextCellEditor",
        'cellStyle': {
            'textAlign'  : 'center',
            'direction'  : 'rtl',
            'white-space': 'normal',
            'word-break' : 'break-word'
        }
    },
    {
        "field"       : "bug",
        'width'       : 50,
        'align'       : 'center',
        "cellRenderer": "DBC_Button_Simple",
        "cellRendererParams": {"color": "success"},
    }
]

cell_conditional_style = {
    "styleConditions": [
        {"condition": "params.value == 'בוצע'"   , "style": {"backgroundColor": "#196A4E", "color": "white"}},
        {"condition": "params.value == 'תקול'"   , "style": {"backgroundColor": "#800000", "color": "white"}},
        {"condition": "params.value == 'בריצה'"  , "style": {"backgroundColor": "#d2e034", "color": "black"}},
        {"condition": "params.value == 'טרם החל'", "style": {"backgroundColor": "dark"   , "color": "white"}},
    ]
}

defaultColDef = {
    # "filter"        : True,
    # "floatingFilter": True,
    "resizable"       : True,
    "sortable"        : True,
    "editable"        : False,
    "minWidth"        : 20,
    'wrapText'        : True,
    'autoHeight'      : True,
    'wrapHeaderText'  : True,
    'autoHeaderHeight': True,
    "cellStyle"       : cell_conditional_style,
}

grid = dag.AgGrid(
    id="testrun-grid",
    # className="ag-theme-alpine-dark",
    # className="ag-theme-alpine headers1",
    # columnSize="autoSize",
    columnSize="sizeToFit",
    className="ag-theme-balham headers1",
    columnDefs=columnDefs,
    rowData=df.to_dict("records"),
    defaultColDef=defaultColDef,
    dashGridOptions={
        "undoRedoCellEditing": True,
        'enableRtl'          : True,
        "rowSelection"       : "single",
        "rowHeight"          : 48,
        'verticalAlign'      : 'middle'
    },
    style={'height': '100%'}
)

header = html.Div("הרצת בדיקה", className="h2 p-2 text-white bg-primary text-center")

app.layout = dbc.Container(
    [
        html.Div(
            [
                dcc.Store(id='moshe-id'),
                header,
                dbc.Row(
                    dbc.Col(
                        html.Div(
                            grid,
                            style={'height': 820}
                        ),
                        className="py-4",
                    )
                ),
                html.Div(id="dbc-btn-simple-value-changed"),
            ],
        )
    ],
)

@app.callback(
    Output("moshe-id"   , "data"            ),
    Input("testrun-grid", "cellValueChanged"),
    Input("testrun-grid", "selectedRows"    ),
    State("testrun-grid", "rowData"         ),
)
def update_testrun_execution(_, row, data):
    # print(ctx.triggered_id)
    if _ is None:
        return dash.no_update
    step_oid  = ObjectId(_.get('data').get('step_oid'))
    test_oid  = ObjectId(_.get('data').get('test_oid'))
    mtp_oid   = ObjectId(_.get('data').get('mtp_oid' ))
    old_value = _.get('old_value')
    new_value = _.get('value'    )
    col_name  = _.get('colId'    )

    result = db.tasks.update_one(
        {'mtp_object.mtp_oid': mtp_oid},
        {
            "$set": {
                f"mtp_object.test_plan.$[plan].test_steps.$[step].{col_name}": new_value
            }
        },
        array_filters=[
            {'plan.test_oid': test_oid},
            {'step.step_oid': step_oid}
        ],
        upsert=True
    )
    print(f'matched: {result.matched_count} modified: {result.modified_count}')

    return None

@app.callback(
    Output("dbc-btn-simple-value-changed", "children"),
    Input("testrun-grid", "cellRendererData"),
)
def show_change(n):
    return json.dumps(n)

if __name__ == "__main__":
    app.run_server(debug=True, port=8050)


"""
    {
        "headerName": "תיאור התקלה",
        "field": "bug_report",
        'width': 200,
        "editable": True,
        "cellEditorPopup": True,
        "cellEditor": "agLargeTextCellEditor",
        'cellStyle': {
            'textAlign': 'right',
            'direction': 'rtl',
            'white-space': 'normal',
            'word-break': 'break-word'
        }
    }
"""