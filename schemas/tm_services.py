import pandas as pd
from schemas.mongo_schema import MongoManager
import dash_bootstrap_components as dbc
from dash import html
from datetime import datetime

task_db = MongoManager('Task')
dt_date = datetime.now()
dt_date = pd.to_datetime(dt_date - pd.DateOffset(months=1)) + pd.offsets.MonthEnd()
dt_date = dt_date.strftime('%Y-%m-%d')

columns_mapping         = {
    '_id'                              :  '_id' ,
    'מס'                               :  'a-01' ,
    'גיליון '                          :  'a-02' ,
    'מתחם (רלוונטי רק למיפוי מתחמים)'  :  'a-03' ,
    'תיאור המשימה'                     :  'a-04' ,
    'הערה'                             :  'a-05' ,
    'סיווג'                            :  'a-06' ,
    'גורם אחראי'                       :  'a-07' ,
    'סטטוס ביצוע'                      :  'a-08' ,
    'תעדוף'                            :  'a-09' ,
    'סטטוס בcdr'                       :  'a-10' ,
    'התייחסות האחראי'                  :  'a-11' ,
    'תאריך פתיחת משימה '               :  'a-12' ,
    'תג"ב'                             :  'a-14' ,
    'שם קובץ מצורף (אם קיים)'          :  'a-15' ,
}
columns_mapping_reverse = {}
for key, value in columns_mapping.items():
    columns_mapping_reverse.update(
        {value: key}
    )

db_object_mapping  = {
    '_id'   :  '_id',
    'a-01'  :  'row_number',
    'a-02'  :  'reference.sheet',
    'a-04'  :  'subject',
    'a-05'  :  'note.main_note',
    'a-07'  :  'user_name.user_object.full_name',
    'a-08'  :  'status',
    'a-09'  :  'priority',
    'a-10'  :  'note',
    'a-11'  :  'owner_notes',
    'a-12'  :  'start',
    'a-14'  :  'finish',
    'a-15'  :  'due_date',
}
data_table_columns = [
    'due_date', 'source', 'priority', 'status', 'u_name', 'wms_domain', 'sheet', 'doctype', 'subject', 'row_number', '_id', 'id',
    'department', 'telephone', 'email', 'role',
]

def fa_text(fa_class: str, text: str) -> dbc.Container:
    return dbc.Container(
        [
            html.P(
                className=fa_class,
                style={
                    'color': '#29abe0',
                    'display': 'inline-block'
                }
            ),
            dbc.Label(
                text,
                className='display-5',
                style={
                    'display': 'inline-block',
                }
            )
        ],
        fluid=True,
        class_name='mt-2 m-0 p-0',
    )

def display_card(header: html.Div, body: html.Div, footer: html.Div) -> dbc.Card:
    card = dbc.Card(
        [
            dbc.CardHeader(
                header,
                class_name='d-grid m-0 p-0',
                style={
                    'text-align': 'center',
                }
            ),
            dbc.CardBody  (
                body,
            ),
            dbc.CardFooter(
                footer,
                class_name='d-grid m-0 p-0',
            )
        ],
        class_name='m-0 p-0'
    )
    return card
