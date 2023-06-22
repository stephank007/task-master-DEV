import os
import dash
import json
import base64
import datetime
import pandas as pd
import plotly.express       as px
import schemas.mongo_schema as ms
import dash_bootstrap_components  as dbc
import dash_ag_grid as dag
from urllib.parse import quote as urlquote
from bson        import ObjectId
from dash        import html, dcc, callback, Input, Output, State, ctx
from dash        import dash_table    as dt
from plotly      import graph_objects as go
from schemas     import tm_services   as sv
from typing      import Tuple, Any
from devtools    import debug
from collections import Counter
from schemas.fields       import Priority, SAPDomainEnum, SAPProcessEnum, Status, StorageType, Severity
from schemas.mongo_schema import timing_decorator, dt_date

# db.collection.createIndex( { "$**": "text" } )
page_number = 0
task_db     = sv.task_db

dash.register_page(
    __name__,
    name='Home Page',
    path='/home'
)
forward = html.Span(
    [
        html.I(className='d-inline-flex fas fa-forward'),
        html.Div('forward', className='d-inline-flex px-2')
    ],
)
backward = html.Span(
    [
        html.Div('backward', className='d-inline-flex px-2'),
        html.I(className='d-inline-flex fas fa-backward'),
    ]
)

domain_ids = {
    'אספקה נכנסת' : '01',
    'אספקה יוצאת' : '02',
    'ניהול המלאי' : '03',
    'ניהול הפצה'  : '04',
    'ניהול החצר'  : '05',
    'תשתיות'      : '06'
}
ban      = '<i class="fas fa-ban     text-mute    mt-3 d-flex flex-row justify-content-center"></i>'
progress = '<i class="fas fa-running text-body    mt-3 d-flex flex-row justify-content-center"></i>'
problem  = '<i class="fas fa-bug     text-white   mt-3 d-flex flex-row justify-content-center"></i>'
done     = '<i class="fas fa-check   text-body    mt-3 d-flex flex-row justify-content-center"></i>'
status_map = {
    Status.P_10: ban,
    Status.P_11: progress,
    Status.P_12: problem,
    Status.P_02: done
}

issue_status = [Status.P_01, Status.P_02, Status.P_03, Status.P_04]
test_status  = [Status.P_10, Status.P_11, Status.P_12, Status.P_02]
m4n_docx     = [Status.P_01, Status.P_15, Status.P_16]
task_types   = {
    'issue': {
        'placeholder': {
            'I_01': 'עדיפות'        ,
            'I_02': 'סימוכין',
            'I_04': 'סטאטוס'        ,
            'I_05': 'due date format: dd/mm/yyyy',
        },
        'status_options': [{'label': _, 'value': _} for _ in issue_status],
        'note_headers': {
            'H0': 'משימה עיקרית',
            'H1': 'הערה ראשית',
            'H2': 'הערה משנית'
        }
    },
    'test': {
        'placeholder': {
            'I_01': 'עדיפות'        ,
            'I_02': 'סימוכין כמו QC',
            'I_04': 'סטאטוס'        ,
            'I_05': 'due date format: dd/mm/yyyy',
        },
        'status_options': [{'label': _, 'value': _} for _ in test_status],
        'note_headers': {
            'H0': 'תיאור הבדיקה',
            'H1': 'מוטיב',
            'H2': 'מורכבות'
        }
    },
    'm4n-docx': {
        'placeholder': {
            'I_01': 'עדיפות',
            'I_02': 'סימוכין',
            'I_04': 'סטאטוס',
            'I_05': 'due date format: dd/mm/yyyy',
        },
        'status_options': [{'label': _, 'value': _} for _ in m4n_docx],
        'note_headers': {
            'H0': 'פיסקה',
            'H1': 'תהליך אב',
            'H2': 'תהליך'
        }
    }
}   # doctype properties

div_hide               = {
    'display': 'none'
}
div_show               = {
    'display': 'block'
}
note_cell_style        = {
    'overflow-y': 'scroll',
    'height'    : 'auto'  ,
    'whiteSpace': 'normal',
    'lineHeight': '15px'  ,
}
note_column_formatting = [
    {
        'if': {
            'column_id': 'note'
        },
        'backgroundColor': 'rgb(240, 240, 240)',
        'border'         : '1px solid rgb(0, 116, 217)',
        'width'          : '10px',
        'textAlign'      : 'right',
        'verticalAlign'  : 'middle',
        'padding'        : '3px'
    }
]
row_style              = {
    'whiteSpace': 'pre-line',
    'maxHeight' : '350px',
    # 'overflow-y': 'scroll',
    'text-align': 'center',
}
dropdown_style         = {
    'textAlign'      : 'right',
    'align-items'    : 'right',
    'justify-content': 'right',
    'font-size'      : 14,
}
header_style           = {
    'backgroundColor': 'rgb(230, 230, 230)',
    'border'         : '1px solid pink',
    'textAlign'      : 'center',
    'fontWeight'     : 'bold',
    'font_size'      : '14px'
}
dropdown_callbacks     = [
    'users-callback'     ,
    'department-callback',
    'status-callback',
    'priority-callback',
    'source-callback',
    'wms-domain-callback'
]
update_pane_callbacks  = [
    'update-priority',
    'update-sheet',
    'update-status',
    'update-due-date',
    'update-owner-note'
]
testplan_dropdown      = {
    'status': {
        'options': [
            {'label': i, 'value': i}
            for i in test_status
        ]
    }
}

priority_values = [{"label": _, "value": _} for _ in Priority.list()      ]
domain_values   = [{"label": _, "value": _} for _ in SAPDomainEnum.list() ]
process_values  = [{"label": _, "value": _} for _ in SAPProcessEnum.list()]
status_values   = [{"label": _, "value": _} for _ in Status.list()        ]

testplan_formatting = [
    {
        'if': {'column_id': c},
        'textAlign': 'center',
        'backgroundColor': 'rgb(240, 240, 240)',
        'width': '10%',
    } for c in ['test_name', 'tester']
]
testplan_formatting.append({
    'if': {'column_id': 'story'},
    'width': '30%',
    'backgroundColor': 'rgb(240, 240, 240)',
    'textAlign': 'right',
})
testplan_formatting.append({
    'if': {'column_id': 'prereq'},
    'width': '30%',
    'backgroundColor': 'rgb(240, 240, 240)',
    'textAlign': 'right',
})
testplan_formatting.append({
    'if': {'column_id': 'status'},
    'width': '15%',
    # 'backgroundColor': 'rgb(240, 240, 240)',
    'backgroundColor': 'whitesmoke',
    'textAlign': 'center',
})
testplan_formatting.append({
    'if': {'column_id': 'symbol'},
    'width': '5%',
    'backgroundColor': 'rgb(240, 240, 240)',
    'textAlign': 'center',
})

test_tables_style_cell = {
    'whiteSpace'     : 'normal',
    'height'         : 'auto',
    'border'         : '1px solid rgb(0, 116, 217)',
    'backgroundColor': 'rgb(231, 235, 224)',
}
test_steps_formatting  = [
    {
        'if': {'column_id': c},
        'backgroundColor': 'rgb(240, 240, 240)',
        'width': '22%',
        'textAlign': 'right',
    } for c in ['subject', 'exp_sap', 'exp_wms']
]
test_steps_formatting.append({
        'if': {'column_id': 'status'},
        'textAlign': 'center',
        'backgroundColor': 'rgb(240, 240, 240)',
        'width': '20%',
    })
test_steps_formatting.append({
        'if': {'column_id': 'symbol'},
        'textAlign': 'left',
        'width': '8%',
        'backgroundColor': 'whitesmoke',
})
test_steps_formatting.append({
        'if': {'column_id': 'step'},
        'textAlign': 'center',
        'backgroundColor': 'whitesmoke',
        # 'backgroundColor': 'rgb(240, 240, 240)',
        'width': '5%',
    })

column_formatting = [
    {
        'if'             : {'column_id': c},
        'textAlign'      : 'right',
        'backgroundColor': 'rgb(240, 240, 240)',
        'width'          : '8%',
    } for c in ['wms_domain', 'status', 'u_name', 'priority', 'due_date', 'sheet']
]
column_formatting.append({
    'if'             : {'column_id': 'doctype'},
    'width'          : '6%',
    'backgroundColor': 'rgb(240, 240, 240)',
    'textAlign'      : 'center',
})
column_formatting.append({
    'if'             : {'column_id': 'row_number'},
    'width'          : '4%',
    'textAlign'      : 'center',
})
column_formatting.append({
    'if'             : {'column_id': 'subject'},
    'backgroundColor': 'rgb(240, 240, 240)',
    'direction'      : 'rtl',
    'width'          : '38%',
})

test_tables_style_header_conditional = [
    {
        'if': {'column_id': 'symbol'},
        'color': 'rgb(230, 230, 230)',
    },
    {
        'if': {'column_id': 'status'},
        'backgroundColor': '#0074D9',
        'color': 'whitesmoke',
    }
]
test_tables_style_data_conditional = [
    {
        'if': {
            # 'column_id': 'exp_wms',
            'filter_query': '{{status}} = {}'.format(Status.P_02)
        },
        'backgroundColor': 'lightgreen',
        'color': 'midnightblue'
    },
    {
        'if': {
            'filter_query': '{{status}} = {}'.format(Status.P_12)
        },
        'backgroundColor': '#85144b',
        'color': 'whitesmoke'
    }
]
table_css  = [
    {                                 # remove toggle_button for the table
        'selector': '.show-hide',
        'rule'    : 'display: none',
    },
]
style_cell = {
    'font-family'    : 'Veranda, sans-serif',
    'fontSize'       : 12,
    'padding'        : '10px',
    'textAlign'      : 'right',
    'text_overflow'  : 'ellipsis',
    'overflow'       : 'hidden',
    'max-width'      : 0,
    'border'         : '1px solid rgb(0, 116, 217)',
    'backgroundColor': 'rgb(231, 235, 224)',
}
style_data = {
    'max-height' : '5px',
}

columns = [
    {'name': 'id'     , 'id': 'id'        },
    {'name': '_id'    , 'id': '_id'       },
    {'name': '#'      , 'id': 'row_number'},
    {'name': 'נושא'   , 'id': 'subject'   },
    {'name': 'סוג'    , 'id': 'doctype'   },
    {'name': 'סימוכין', 'id': 'sheet'     },
    {'name': 'WMS'    , 'id': 'wms_domain'},
    {'name': 'אחראי'  , 'id': 'u_name'    },
    {'name': 'סטטוס'  , 'id': 'status'    },
    {'name':  'עדיפות', 'id': 'priority'  },
    {'name': 'מקור'   , 'id': 'source'    },
    {'name': 'תג״ב'   , 'id': 'due_date'  },
][::-1]

datatable  = dt.DataTable(
    id='task-table',
    columns=columns,
    # columns=[{'name': i, 'id': i, 'deletable': False} for i in sv.data_table_columns],
    hidden_columns=['_id', 'id', 'source', 'department', 'telephone', 'email', 'role'],
    row_selectable='single'   ,
    page_action='native'      ,
    page_current=0            ,
    page_size=ms.PAGE_SIZE    ,
    editable=False            ,
    style_header=header_style ,
    style_data= style_data    ,
    style_cell= style_cell    ,
    css=table_css             ,
    style_cell_conditional=column_formatting,
    # filter_action='native'  ,
    # sort_action='native'    ,
    # export_format='xlsx'    ,
    # export_headers='display',
)
top_row_form   = dbc.Form(dbc.Row([
    dbc.Col(
        dbc.InputGroup(
            [
                dbc.Input(
                    id='search-input',
                    debounce=True,
                    type='search',
                    placeholder="יש להתחיל בחיפוש... כמו בגוגל",
                    class_name='border border-primary border-start-0 rounded-0 g-2 mt-3',
                ),
                dbc.Button(
                    type='button',
                    class_name='border border-primary border-end-0 rounded-0 btn btn-primary fa-solid fa-magnifying-glass g-2 mt-3',
                    color='light'
                )
            ],
        ),
        className="me-3",
    ),
    dbc.Col(
        html.Div(id='search-feedback'),
        className='me-3 text-center g-0 shadow p-1 mb-2 bg-body rounded',
    ),
    dbc.Col(
        html.Div(id='filter-feedback'),
        class_name='me-3 text-center g-0 shadow p-1 mb-2 bg-body rounded',
    ),
]))  # className="shadow p-1 mb-2 bg-body rounded",

def update_form(record_type: str):
    placeholder    = task_types.get(record_type).get('placeholder'   )
    status_options = task_types.get(record_type).get('status_options')
    first_row = dbc.Row(
        [
            dbc.Col(
                dbc.Input(
                    id="update-sheet",
                    placeholder=placeholder.get('I_02'),
                    size='md',
                    debounce=True,
                    class_name='mb-3 border border-secondary text-secondary',
                ),
                className="me-3 mt-3",
            ),
            dbc.Col(
                dbc.Select(
                    id="update-priority",
                    placeholder=placeholder.get('I_01'),
                    size='md',
                    class_name='mb-3 border border-secondary text-secondary',
                    options=priority_values
                ),
                className="me-3 mt-3",
            ),
            dbc.Col(
                dbc.Select(
                    id="update-status",
                    placeholder=placeholder.get('I_04'),
                    size='md',
                    class_name='mb-3 mt-3 border border-secondary text-secondary',
                    options=status_options
                ),
                className="me-3",
            ),
            dbc.Col(
                html.Div(
                    dbc.Input(
                        id="update-due-date",
                        type='text',
                        debounce=True,
                        placeholder=placeholder.get('I_05'),
                        size='md',
                        class_name='text-start mb-3 mt-3 border border-secondary text-secondary',
                    ),
                    dir='ltr'
                ),
                className="me-3 ms-3",
            )
        ],
    )
    second_row = dbc.Row(
        [
            dbc.Col(
                dbc.InputGroup(
                    [
                        dbc.Button(
                            type='button',
                            class_name='btn bg-white btn-primary fa-solid fa-edit fa-2xl mb-3 border border-secondary',
                            color='light'
                        ),
                        dbc.Textarea(
                            id='update-owner-note',
                            placeholder='הערות האחראי',
                            debounce=True,
                            size='md',
                            class_name='mb-3 border border-secondary text-secondary',
                        ),
                    ]
                ),
                className="me-3 col-5",
            ),
            dbc.Col(
                html.Div(
                    dbc.Button(
                        "עדכון",
                        id='update-button',
                        size="lg",
                        class_name="h-100 me-1 mt-1",
                        color='dark',
                    ),
                    className='shadow p-1 mb-1 bg-body rounded d-grid'
                ),
                class_name='col-2'
            ),
            dbc.Col(
                html.Div(id='update-result', className='text-center')
            )
        ],
        justify='center',
    )
    all_rows =  dbc.Container(
        [
            first_row,
            second_row,
            html.Hr(),
            # html.Div(style={'height': 1400}),
        ], fluid=True
    )
    return all_rows

def dropdown_menus(items_list: list, label: str, dropdown_callback: str) -> dbc.Col:
    dropdown = dbc.Col(
        dbc.DropdownMenu(
            id=dropdown_callback,
            label=label,
            size='sm',
            children=items_list,
            className='d-grid gap-2',
        ),
    )
    return dropdown

def dcc_dropdown(items_list: list, label: str, dropdown_callback: str) -> dbc.Col:
    dropdown = dbc.Col(
        html.Div(
            dcc.Dropdown(
                id=dropdown_callback,
                options=items_list,
                placeholder=label + ' ...',
                searchable=True,
                optionHeight=26,
            ),
            style=dropdown_style,
            lang='he',
            dir='rtl'
        ), width={'size': 2, 'offset': 0}
    )
    return dropdown

def draw_charts(df1: pd.DataFrame, df2: pd.DataFrame) -> html.Div:
    people   = df1.copy()
    past_due = df2.copy()
    n1 = 'אבי פרישמן'
    n2 = 'לירן מרום'

    if len(people) > 0:
        people = people[~people['u_name'].isin([n1, n2])]
        fig_pie = px.pie(
            people,
            values='count',
            names='status',
            hole=.3,
            color='status',
            color_discrete_map={
                'פתוח'  : 'crimson',
                'בוצע'  : 'darkgreen',
                'מבוטל' : 'lightblue',
                'עתידי' : 'grey'
            },
            height=400,
        )
        fig_pie.update_traces(textinfo='value')
        fig_pie.update_layout(
            title_text='Status',
            title_x=0.42,
            margin=dict(l=0, r=0, t=30, b=10),
            uniformtext_minsize=16,
            uniformtext_mode='hide',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
    else:
        fig_pie = go.Figure()

    #### bar chart
    if len(people) > 0:
        fig_bar = px.bar(
            people,
            x='count',
            y='u_name',
            color='status',
            text='status',
            orientation='h',
            height=400,
            color_discrete_map={
                'פתוח'  : 'crimson',
                'בוצע'  : 'darkgreen',
                'מבוטל' : 'lightblue',
                'עתידי' : 'grey'
            },
        )
        fig_bar.update_layout(
            #  title_text='Status',
            title_x=0.42,
            margin=dict(l=0, r=0, t=0, b=0),
            uniformtext_minsize=12,
            uniformtext_mode='hide',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        fig_bar.update_xaxes(title=None)
        fig_bar.update_yaxes(title=None)
    else:
        fig_bar = go.Figure()

    if len(past_due) > 0:
        past_due = past_due[~past_due['u_name'].isin([n1, n2])]
        fig_pd = px.bar(
            past_due,
            x='count',
            y='u_name',
            text='count',
            orientation='h',
            height=400,
            color_discrete_sequence=['crimson']
        )
        fig_pd.update_layout(
            title_text='Past Due',
            title_y=0.97,
            margin=dict(l=0, r=0, t=0, b=0),
            uniformtext_minsize=12,
            uniformtext_mode='hide',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        fig_pd.update_xaxes(title=None)
        fig_pd.update_yaxes(title=None)
    else:
        fig_pd = go.Figure()

    charts = html.Div(  # charts
        id='moshe',
        children=[
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            dcc.Graph(id='pie-chart', figure=fig_pie),
                            style={'border': '1px solid #f47c3c'}
                        ), className='col-4 m-0'
                    ),
                    dbc.Col(
                        html.Div(
                            dcc.Graph(id='bar-chart', figure=fig_bar),
                            style={'border': '1px solid #f47c3c'}
                        ), class_name='col-4 m-0'
                    ),
                    dbc.Col(
                        html.Div(
                            dcc.Graph(id='pdu-chart', figure=fig_pd),
                            style={'border': '1px solid #f47c3c'}
                        ), class_name='col-4 m-0'
                    )
                ],
                justify='center'
            ),
        ],
        dir='rtl',
        style={'border': '1px solid #f47c3c'}
    )
    return charts

def fa_feedback(page: int, pages: int) -> html.Div:
    return html.Div(
        [
            # dbc.Label(f'page {page} out of {pages + 1}', class_name='fs-5 text-dark my-0'),
            # dbc.Label(class_name='fas fa-comments mx-1 my-0'),
            html.P(f'page {page} out of {pages + 1}', className='fs-5 text-dark my-0'),
            html.P(className='fas fa-comments mx-1 my-0 text-center'),
        ],
        className='d-flex flex-row justify-content-center'
    )

def fa_documents_number(documents: int) -> html.Div:
    return html.Div(
        [
            dbc.Label(f'{documents} documents found', class_name='fs-5 text-dark my-0'),
            dbc.Label(className='fas fa-files fa-lg mx-1 text-dark my-0'),
        ]
    )

def fa_rendering(text: str, symbol: str) -> list:
    return [
        dbc.Label(className=symbol),
        dbc.Label(text, class_name='s-5 text-white mt-3'),
    ]

def diff_dashtable(data, data_previous, row_id_name=None):
    dff, df_previous = pd.DataFrame(data=data), pd.DataFrame(data_previous)

    if row_id_name is not None:
        # If using something other than the index for row id's, set it here
        for _df in [dff, df_previous]:
            # Why do this?  Guess just to be sure?
            assert row_id_name in _df.columns
            _df = _df.set_index(row_id_name)
    else:
        row_id_name = 'index'

    df_mask = ~((dff == df_previous) | ((dff != dff) & (df_previous != df_previous)))
    df_mask = df_mask.loc[df_mask.any(axis=1)]

    changes = []
    # This feels like a place I could speed this up if needed
    for idx, row in df_mask.iterrows():
        row_id = row.name

        # Act only on columns that had a change
        row = row[row.eq(True)]
        for change in row.items():
            changes.append(
                {
                    row_id_name     : row_id,
                    'column_name'   : change[0],
                    'current_value' : dff.at[row_id, change[0]],
                    'previous_value': df_previous.at[row_id, change[0]],
                }
            )
    return changes

def testrun_status(child_status: list) -> Status:
    my_map = {
        0: Status.P_02,
        1: Status.P_12,
        2: Status.P_10
    }
    completed   = Counter(child_status).get(Status.P_02) == len(child_status)
    has_bug     = True if Counter(child_status).get(Status.P_12) else False
    not_started = Counter(child_status).get(Status.P_10) == len(child_status)

    t = [completed, has_bug, not_started]
    status_key = [i for i, x in enumerate(t) if x]
    return Status.P_11 if not status_key else my_map[status_key[0]]

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

def save_file(name, content):
    """Decode and store a file uploaded with Plotly Dash."""
    data = content.encode("utf8").split(b";base64,")[1]
    # name = f'{datetime.datetime.now()}-{name}'
    with open(name, "wb") as fp:
        fp.write(base64.decodebytes(data))

def uploaded_files(file_directory):
    """List the files in the upload directory."""
    files = []
    for filename in os.listdir(file_directory):
        files.append(filename)
        fn = file_directory.joinpath(filename).as_posix()
        try:
            with open(fn, 'rb') as fr:
                moshe_1 = fr.read()
        except Exception as ex:
            print(ex)

        if os.path.isfile(fn):
            files.append(filename)
        else:
            print(fn, 'is not a file')
    return files

def file_download_link(filename, file_directory):
    """Create a Plotly Dash 'A' element that downloads a file from the app."""

    fn = file_directory.joinpath(filename).as_posix()
    location = "/download/{}".format(urlquote(filename))
    return html.A(filename, href=location)

def encode_image(image_path):
    with open(image_path, 'rb') as file:
        encoded_string = base64.b64encode(file.read()).decode('utf-8')
    return encoded_string

######################################################################################################################
def layout():
    return dbc.Container([
        html.Div(
            [
                dcc.Location(id="direction-home"   , refresh=True         ),
                dcc.Location(id="url-testrun-step", refresh="callback-nav"),
                dcc.Store(id='filters-query'     ),
                dcc.Store(id='clicked-chart'     ),
                # dcc.Store(id='previous-dropdowns'),
                dcc.Store(id='diff-store'        ),
                dcc.Store(id='mtp-test-plans'    ),
                dcc.Store(id='testrun-grid-data' ),
                dcc.Store(id='moshe-id'),
                html.Br(),
                top_row_form,
                html.Br(),
                dbc.Row( # dropdowns
                    [
                        dcc_dropdown(items_list=[], label='אחראי'   , dropdown_callback=dropdown_callbacks[0]),
                        dcc_dropdown(items_list=[], label='מחלקה'   , dropdown_callback=dropdown_callbacks[1]),
                        dcc_dropdown(items_list=[], label='סטטוס'   , dropdown_callback=dropdown_callbacks[2]),
                        dcc_dropdown(items_list=[], label='עדיפות'  , dropdown_callback=dropdown_callbacks[3]),
                        dcc_dropdown(items_list=[], label='מקור'    , dropdown_callback=dropdown_callbacks[4]),
                        dcc_dropdown(items_list=[], label='תהליך אב', dropdown_callback=dropdown_callbacks[5]),
                    ],
                ),
            ],
            dir='rtl',
            lang='he'
        ),
        dbc.Row(
            [
                dbc.Col(
                    html.Div(
                        [
                            dbc.Button(
                                children=forward,
                                id='page-next', type='submit', color='primary',
                                className='ms-2'
                                # className='fa-solid fa-forward g-2 m-2'
                            ),
                            dbc.Tooltip('next page', target='page-next', placement='bottom'),
                            dbc.Button(
                                children=backward,
                                id='page-prev', type='submit', color='primary',
                                # className='fa-solid fa-backward g-2 m-2'
                            ),
                            dbc.Tooltip('previous page', target='page-prev', placement='bottom'),
                        ]
                    )
                ),
            ]
        ),
        html.Div(
            dcc.Loading(
                [
                    html.Div(id='spinner-roll'   ),
                    html.Div(datatable, dir='ltr'),
                ]
            )
        ),
        html.Div(
            id='task-edit-container',
            children=[
                dbc.Row(
                    [
                        dbc.Col(
                            html.Div(id='record-info'),
                            class_name='col-10'
                        ),
                        dbc.Col(
                            html.Div(
                                [
                                    dbc.Button(
                                        id='switch-pane',
                                        type='submit',
                                        class_name='btn btn-secondary fs-2 fas fa-window-close mt-2'
                                    ),
                                    dbc.Tooltip('close pane', target='switch-pane', placement='bottom'),
                                ], className='text-start',
                            ),
                        )
                    ],
                    class_name='bg-secondary my-2 mx-1'
                ),
                dbc.Row(
                    id='document-detail-row',
                    class_name='m-0 overflow-auto border border-warning',
                ),
            ],
            dir='rtl',
            lang='he',
        ),
        html.Div(id='document-locked'),
        html.Div(id='update-form'),
        html.Hr(),
        html.Div(id='test-detail-pane'),
        html.Div(id='charts-pane'),
    ], fluid=True)
######################################################################################################################

@callback(
    Output('task-edit-container', 'style'),
    Output('record-info'        , 'style'),
    Output('update-form'        , 'style'),
    Output('charts-pane'        , 'style'),

    Input ('switch-pane',      'n_clicks'),
    Input ('task-table' , 'selected_rows'),
)
def pane_manger(selected, clicked: int):
    if ctx.triggered_id == 'task-table' and ctx.inputs.get('task-table.selected_rows'):
        return div_show, div_show, div_show, div_hide
    else:
        return div_hide, div_hide, div_hide, div_show

@callback(
    Output('bug-report-switch'      , 'style'           ),
    Input ('switch-bug-close-button', 'n_clicks'        ),
    Input ('testrun-grid'           , 'cellRendererData')
)
def bug_pane_manager(n1, n2):
    moshe_0 = ctx.inputs
    moshe_1 = ctx.triggered
    moshe_2 = ctx.states

    print(ctx.triggered_id, ctx.triggered[0].get('value'))
    triggered_column = None
    if not ctx.triggered_id:
        return dash.no_update

    if ctx.triggered_id == 'testrun-grid' and ctx.triggered[0].get('value') is not None:
        triggered_column = ctx.triggered[0].get('value').get('colId')

    if triggered_column == 'report':
        return div_show

    if ctx.triggered_id == 'testrun-grid' and ctx.triggered[0].get('value') is None:
        return div_hide

    if ctx.triggered_id == 'switch-bug-close-button':
        return div_hide

@callback(
    Output('spinner-roll', 'children'     ),
    Input ('task-table'  , 'loading_state')
)
def on_loading(state):
    return

@callback(
    Output('direction-home', 'href'),
    Input('active-user'    , 'data'),
)
def authentication_check(active_user):
    # print(f'-->{active_user.get("full_name")}<--')
    if not active_user:
        return '/direction-home'
    else:
        return dash.no_update

@callback(
    Output('task-table', 'style_data_conditional'       ),
    Input ('task-table', 'derived_virtual_selected_rows')
)
def highlight_selected_task(selected_row):
    if selected_row is None:
        return dash.no_update
    else:
        return [
            {
                'if': {
                    'filter_query': '{{id}} = {}'.format(i)
                },
                # 'backgroundColor': 'midnightblue',
                'backgroundColor': '#0074D9',
                'color'          : 'whitesmoke',
            }
            for i in selected_row
        ]

@callback(
    # dropdowns
    Output('users-callback'     , 'options'),
    Output('department-callback', 'options'),
    Output('status-callback'    , 'options'),
    Output('priority-callback'  , 'options'),
    Output('source-callback'    , 'options'),
    Output('wms-domain-callback', 'options'),
    #
    Output('task-table'         , 'data'    ),
    Output('charts-pane'        , 'children'),
    Output('search-feedback'    , 'children'),
    Output('filter-feedback'    , 'children'),
    Output('page-next'          , 'n_clicks'),
    Output('page-prev'          , 'n_clicks'),
    Output('filters-query'      , 'data'    ),
    # Output('previous-dropdowns' , 'data'    ),

    # Input ('previous-dropdowns' , 'data'    ),
    Input ('filters-query'      , 'data'    ),
    Input ('clicked-chart'      , 'data'    ),
    Input ('page-next'          , 'n_clicks'),
    Input ('page-prev'          , 'n_clicks'),
    Input ('search-input'       , 'value'   ),
    [Input(v_callback, 'value') for v_callback in dropdown_callbacks],
    Input ('switch-pane'        , 'n_clicks'),
)
@timing_decorator
# def documents_portal(previous_dropdowns, filters_query, clicked_chart, b_next, b_prev, search_input, *args):
def documents_portal(filters_query, clicked_chart, b_next, b_prev, search_input, *args):
    if ctx.triggered_id == 'clicked-chart':
        filter_dict = filters_query.copy()
        filter_dict.update({'status': None})

        clicked_data    = clicked_chart.get('selection')
        triggered_chart = clicked_chart.get('chart'    )
        match triggered_chart:
            case 'pdu':
                filter_dict.update(
                    {
                        'status'   : Status.P_01,
                        'due_date' : {'$lt': dt_date},
                        'full_name': clicked_data
                    }
                )
            case 'bar':
                filter_dict.update(
                    {
                        'status'   : clicked_chart.get('status'   ),
                        'full_name': clicked_chart.get('selection')
                    }
                )
            case 'pie':
                filter_dict.update({'status': clicked_data})
            case _:
                filter_dict.update({'status': None})
    else:
        filter_dict = {
            'search'           : search_input,
            'full_name'        : args[0],
            'department'       : args[1],
            'status'           : args[2],
            'priority'         : args[3],
            'reference.source' : args[4],
            'wms_object.domain': args[5]
        }

    if ctx.triggered_id not in ['page-next', 'page-prev']:
        b_next = 0
        b_prev = 0
    else:
        filter_dict = filters_query

    if ctx.triggered_id == 'page-prev':
        b_next = max(0, b_next-1)
    skip = b_next

    xn = 1 if b_next else 0
    xp = 1 if b_prev else 0
    next_or_prev_selected = bool(xn | xp)

    display_charts = html.Div()
    dropdown_options = None
    if next_or_prev_selected:   # this is for next and prev pages
        filters_1 = filter_dict.copy()
        df_tasks, documents = task_db.grand_filter_query(collection='tasks', grand_filter=filters_1, skip=skip)
        # dropdown_options    = previous_dropdowns
    else:
        filters_2 = filter_dict.copy()
        results   = task_db.multi_facet_query (collection='tasks', grand_filter=filters_2)

        results          = list(results)
        dropdown_options = results[0]
        charts_dff       = results[1]
        past_due_dff     = results[2]
        documents        = results[3]
        df_tasks         = results[4]

        # condition for the displaying charts
        if len(df_tasks) > 0:
            display_charts = draw_charts(df1=charts_dff, df2=past_due_dff)

    pages        = int(documents/ms.PAGE_SIZE)
    current_page = b_next + 1
    feedback     = dbc.Alert(fa_feedback(page=current_page, pages=pages), color='info', class_name='g-1')

    # empty results
    if len(df_tasks) == 0:
        message = dbc.Alert(f'סליחה, יש לחדש חיפוש לא נמצאו ממצאים', color='danger', class_name='g-1' )
        return [], [], [], [], [], [], None, display_charts, message, feedback, b_next, b_prev, filter_dict #, dropdown_options

    message   = dbc.Alert(fa_documents_number(documents=documents), color='success', class_name='g-1')
    records = df_tasks.to_dict('records')

    return \
        dropdown_options[0], \
        dropdown_options[1], \
        dropdown_options[2], \
        dropdown_options[3], \
        dropdown_options[4], \
        dropdown_options[5], \
        records            , \
        display_charts, message, feedback, b_next, b_prev, filter_dict # , dropdown_options

@callback(
    Output('document-detail-row', 'children'     ),
    Output('record-id'          , 'data'         ),
    Output('owner-name'         , 'data'         ),
    Output('record-info'        , 'children'     ),
    Output('task-table'         , 'selected_rows'),
    Output('update-form'        , 'children'     ),
    Output('test-detail-pane'   , 'children'     ),
    Output('mtp-test-plans'     , 'data'         ),

    Input ('switch-pane'        , 'n_clicks'     ),
    Input ('task-table'         , 'selected_rows'),
    State ('task-table'         , 'data'         ),
) # issue and testplan layouts
def document_master_portal(switch_pane, selected_row, rows):  # renders the update pane and test execution
    """
    her we manage the sorts of doctype update flow. main focus is given to test flow
    :param switch_pane:
    :param selected_row: from task-table
    :param rows:
    :return:
        document_detail_row, selected_id, owner_name, record_info,
        input_row, update_form_by_record_type, mtp_layout, t_plans
    """
    def create_md_note(header: str, note: str, oid: Any) -> dbc.Col:
        if note is None:
            return dbc.Col(html.Div([html.H6(header, style={'margin-bottom': '0px'}),]))

        note_lines = pd.DataFrame(data=note.split('\n'), columns=[header])
        note_lines[header] = note_lines[header].str.strip()
        note_lines['oid'] = oid
        mask = note_lines.copy()[header].astype('bool')
        note_lines = note_lines[mask]

        match header:
            case 'תאריך עדכון':
                table = dt.DataTable(
                    id='owner-date-table',
                    columns=[{'name': i, 'id': i} for i in note_lines.columns],
                    data=note_lines.to_dict('records'),
                    hidden_columns=['oid'],
                    row_selectable='single',
                    style_header=header_style,
                    style_cell_conditional=note_column_formatting,
                    style_cell=note_cell_style,
                    style_table={'margin-top': '0px'},
                    css=[{'selector': '.show-hide', 'rule': 'display: none'}]
                )
            case 'הערת אחראי':
                note_lines['oid' ] = oid['id']
                note_lines['date'] = oid['date']
                table = dt.DataTable(
                    id='owner-notes',
                    columns=[{'name': i, 'id': i} for i in note_lines.columns],
                    # data=note_lines.to_dict('records'),
                    hidden_columns=['oid', 'date'],
                    style_header=header_style,
                    style_cell_conditional=note_column_formatting,
                    style_cell=note_cell_style,
                    style_table={'margin-top': '0px'},
                    css=[{'selector': '.show-hide', 'rule': 'display: none'}]
                )
            case _:
                table = dt.DataTable(
                    columns=[{'name': i, 'id': i} for i in note_lines.columns],
                    data=note_lines.to_dict('records'),
                    hidden_columns=['oid'],
                    style_header=header_style,
                    style_cell_conditional=note_column_formatting,
                    style_cell=note_cell_style,
                    style_table={'margin-top': '0px'},
                    css=[{'selector': '.show-hide', 'rule': 'display: none'}]
                )

        note_layout = dbc.Col(
            html.Div(table),
            class_name='col-2 mt-0',
            style=row_style
        )
        return note_layout

    def simple_table_renderer(records: list) -> dt.DataTable:
        dff = pd.DataFrame(records)

        return dt.DataTable(
            columns=[{'name': i, 'id': i} for i in dff.columns],
            data=dff.to_dict('records'),
            hidden_columns=['oid'],
            style_header=header_style,
            style_cell_conditional=note_column_formatting,
            style_cell=note_cell_style,
            style_table={'margin-top': '0px'},
            css=[{'selector': '.show-hide', 'rule': 'display: none'}]
        )

    def testplan_table_renderer(test_plans: list) -> dt.DataTable:  # layout of the test panes and test grids
        dff = pd.DataFrame(test_plans)
        dff.drop(['test_steps'], inplace=True, axis=1)

        t_columns = [{'name': i, 'id': i} for i in dff.columns]
        dff['id' ] = dff.index
        dff['bug'] = ''
        #### AG-GRID for testplan table ##############################################################################
        cell_conditional_style = {
            "styleConditions": [
                {"condition": "params.value == 'בוצע'"   , "style": {"backgroundColor": "#196A4E", "color": "white"}},
                {"condition": "params.value == 'תקול'"   , "style": {"backgroundColor": "#800000", "color": "white"}},
                {"condition": "params.value == 'בריצה'"  , "style": {"backgroundColor": "#d2e034", "color": "black"}},
                {"condition": "params.value == 'טרם החל'", "style": {"backgroundColor": "dark"   , "color": "white"}},
            ]
        }
        columnDefs             = [
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
                "headerName": "#",
                "field": "test_name",
                'width': 80,
                'cellStyle': {
                    'direction': 'rtl',
                    'white-space': 'normal',
                    'word-break': 'break-word'
                }
            },
            {
                "headerName": "תיאןר הבדיקה",
                "field": "story",
                'width': 120,
                'cellStyle': {
                    'textAlign': 'right',
                    'direction': 'rtl',
                    'white-space': 'normal',
                    'word-break': 'break-word'
                }
            },
            {
                "headerName": "דרישת קדם",
                "field": "prereq",
                'width': 120,
                'cellStyle': {
                    'textAlign': 'right',
                    'direction': 'rtl',
                    'white-space': 'normal',
                    'word-break': 'break-word'
                }
            },
            {
                "headerName": "בודק",
                "field": "tester",
                'width': 75,
                "editable": True,
                "cellEditor": "agSelectCellEditor",
                "cellEditorParams": {
                    "values": [Status.P_10, Status.P_11, Status.P_12, Status.P_02],
                },
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
                "headerName": "מספר קטלוגי",
                "field": "catalog",
                'width': 75,
                "editable": True,
            },
            {
                "headerName": "משק",
                "field": "storage_type",
                'width': 75,
                "editable": True,
                "cellEditor": "agSelectCellEditor",
                "cellEditorParams": {
                    "values": [
                        StorageType.s1, StorageType.s2, StorageType.s3,
                        StorageType.s4, StorageType.s5, StorageType.s6
                    ],
                },
            },
            {
                "headerName": "הערות",
                "field": "comments",
                'width': 120,
                "editable": True,
                "cellEditorPopup": True,
                "cellEditor": "agLargeTextCellEditor",
                'cellStyle': {
                    'textAlign': 'center',
                    'direction': 'rtl',
                    'white-space': 'normal',
                    'word-break': 'break-word'
                }
            },
            {
                "headerName": "צפייה בתקלות",
                "field": "bug",
                'width': 50,
                'align': 'center',
                "cellRenderer": "DBC_Button",
                "cellRendererParams": {
                    "rightIcon": "fas fa-bug mt-1",
                    "outline": True,
                    "color": "primary"
                },
            }
        ]
        defaultColDef          = {
            # "filter"        : True,
            # "floatingFilter": True,
            "resizable": True,
            "sortable": True,
            "editable": False,
            "minWidth": 20,
            'wrapText': True,
            'autoHeight': True,
            'wrapHeaderText': True,
            'autoHeaderHeight': True,
            "cellStyle": cell_conditional_style,
        }
        jacob_0 = dag.AgGrid(
            id="testplan-grid",
            columnSize="sizeToFit",
            className="ag-theme-balham headers1",
            columnDefs=columnDefs,
            rowData=dff.to_dict("records"),
            defaultColDef=defaultColDef,
            dashGridOptions={
                "undoRedoCellEditing": True,
                'enableRtl'          : True,
                "rowSelection"       : "single",
                "rowHeight"          : 48,
                'verticalAlign'      : 'middle'
            },
            style = {'height': '100%'}
            # style={'height': 375}
        )

        bug_report_columns_def = [
            {
                "headerName": "עדיפות",
                "field": "priority",
                'width': 150,
                "editable": True,
                "cellEditor": "agSelectCellEditor",
                "cellEditorParams": {"values": [Priority.S_01, Priority.S_02, Priority.S_03, Priority.S_04]},
            },
            {
                "headerName": "חמרה",
                "field": "severity",
                'width': 150,
                "editable": True,
                "cellEditor": "agSelectCellEditor",
                "cellEditorParams": {"values": [Priority.S_01, Priority.S_02, Priority.S_03, Priority.S_04]},
            },
            {
                "headerName": "הערות",
                "field": "comments",
                'width': 180,
                "editable": True,
                "cellEditorPopup": True,
                "cellEditor": "agLargeTextCellEditor",
                'cellStyle': {
                    'textAlign': 'center',
                    'direction': 'rtl',
                    'white-space': 'normal',
                    'word-break': 'break-word'
                }
            }
        ]
        bug_record = {
            'priority': Priority.S_01,
            'severity': Severity.S_01,
        }
        bug_dff = pd.DataFrame([bug_record])

        bug_report_grid = dag.AgGrid(
            id="bug-report-grid",
            columnSize="sizeToFit",
            className="ag-theme-balham headers1",
            columnDefs=bug_report_columns_def,
            rowData=bug_dff.to_dict("records"),
            defaultColDef=defaultColDef,
            dashGridOptions={
                "undoRedoCellEditing": True,
                'enableRtl': True,
                "rowSelection": "single",
                "rowHeight": 48,
                'verticalAlign': 'middle'
            },
            # style={'height': '100%'}
            style={'height': 150}
        )
        # TODO: Please add callback and insert a bug report object to the testrun row

        bug_report_layout = html.Div(
            id='bug-report-switch',
            children=[
                dbc.Row(
                    dbc.Col(
                        html.Div(
                            [
                                dbc.Button(
                                    id='switch-bug-close-button',
                                    type='submit',
                                    class_name='btn btn-danger fs-2 fas fa-window-close mt-2'
                                ),
                                dbc.Tooltip('close bug pane', target='switch-bug-pane', placement='bottom'),
                            ], className='text-start',
                        ),
                    ),
                    class_name='bg-danger my-2 mx-1'
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            html.Div(bug_report_grid),
                            # class_name='m-0 overflow-auto border border-warning',
                            class_name = 'col-4',
                        ),
                        dbc.Col(
                            dbc.Button(
                                'הצג ושלח דו״ח תקלה',
                                id='report-bug-button',
                                outline=True,
                                color='danger',
                                class_name='ml-auto'
                            ),
                            className='d-grid, col-3 fs-3'
                        )
                    ]
                ),
                dbc.Row(
                    dbc.Col(
                        dbc.Modal(
                            [
                                dbc.ModalHeader(
                                    dbc.Alert("דוח תקלה", color='info', class_name='fs-3'),
                                ),
                                dbc.ModalBody(
                                    html.Div(
                                        dcc.Markdown(
                                            """
                                            # Hello World
                                            """
                                        ),
                                        lang='he', dir='rtl'
                                    ),
                                ),
                                dbc.ModalFooter(
                                    dbc.Button(
                                        "Close",
                                        id="close-bug-report-button",
                                        class_name="ml-auto"
                                    )
                                ),
                            ],
                            id="display-bug-report", size='xl'
                        )
                    )
                )
            ],
            style={'display': 'none'}
        )
        #### AG-GRID for testplan table ##############################################################################
        return jacob_0, bug_report_layout

    def testplan_layout(db_document: dict, symbol: str) -> list:
        top_row, info_row, t_name = issue_layout(
            db_document=db_document,
            symbol=symbol
        )

        cycle      = db_document.get('reference'  ).get('secret_1'  )
        mtp_id     = db_document.get('mtp_object').get('mtp_id'     )
        prod_key   = db_document.get('mtp_object').get('product_key')
        complexity = db_document.get('mtp_object').get('complexity' )
        bp_rns     = db_document.get('mtp_object').get('BP_RN'      )
        chapters   = db_document.get('mtp_object').get('CDR'        )
        purpose    = db_document.get('mtp_object').get('purpose'    )
        systems    = db_document.get('mtp_object').get('systems'    )
        test_plans = db_document.get('mtp_object').get('test_plan'  )

        for i, plan in enumerate(test_plans):
            test_plans[i].update(
                {
                    'mtp_oid' : str(test_plans[i].get('mtp_oid' )),
                    'test_oid': str(test_plans[i].get('test_oid')),
                }
            )

        testplan, bug_report_layout = testplan_table_renderer(test_plans=test_plans)
        first_row = dbc.Row(
            [
                dbc.Col(
                    dbc.Alert(f'סבב בדיקות: {cycle}', color='secondary', class_name='fs-3 text-center'),
                    class_name='col-6 m-0 g-0'
                ),
                dbc.Col(
                    dbc.Alert(f'מזהה תכנית הבדיקה: {mtp_id}'   , color='secondary', class_name='fs-3 text-center'),
                    class_name='col-6 m-0 g-0'
                )
            ]
        )
        second_row = dbc.Row(  # תכלית בדיקה
            dbc.Col(
                html.Div(
                    [
                        html.Div(
                            dbc.Button(
                                'הצג MTP',
                                id='display-purpose-modal-button',
                                outline=True,
                                color='info',
                                class_name='ml-auto'
                            ),
                            className='d-grid'
                        ),
                        dbc.Modal(
                            [
                                dbc.ModalHeader(
                                    dbc.Alert("פירוט מטרת הבדיקה", color='info', class_name='fs-3'),
                                ),
                                dbc.ModalBody(
                                    html.Div(
                                        simple_table_renderer(purpose),
                                        lang='he', dir='rtl'
                                    ),
                                ),
                                dbc.ModalFooter(
                                    dbc.Button(
                                        "Close",
                                        id="close-purpose-modal-button",
                                        class_name="ml-auto"
                                    )
                                ),
                            ],
                            id="display-purpose-modal", size='lg'
                        )
                    ]
                ),
            ),
            class_name='col-2'
        )
        third_row = dbc.Row(
            [
                dbc.Col(
                    html.Div(
                        [
                            dbc.Alert('תכנית הבדיקות', class_name='fs-3'),
                            # testplan_table_renderer(test_plans=test_plans),
                            testplan
                        ],
                        style={'height': 250}
                    ),
                    class_name='col mt-0',
                    style=row_style
                ),

            ],
            justify='center',
            class_name='mt-1'
        )
        fourth_row = html.Div(
            [
                dbc.Alert('הרצת הבדיקה', class_name='fs-3 text-center'),
                bug_report_layout,
                html.Div(id='testrun-grid-div', style={'height': 820}),
                dbc.Modal(
                    [
                        dbc.ModalHeader("More information about selected row"),
                        dbc.ModalBody(id="file-handler-modal-content"),
                        dbc.ModalFooter(
                            dbc.Button(
                                "Close",
                                id="close",
                                className="ml-auto"
                            )
                        ),
                        html.Div(id='uploaded-image-div', style={'max-width': '450px'})
                    ],
                    id="file-handler-modal", size='xl'
                ),
            ]
        )

        m_layout = html.Div(id='testplan-layout', children=[
                first_row ,
                second_row,
                third_row ,
                fourth_row,
                html.Div(id='testrun-value-changed'),
                html.Div(style={'height': 200})
            ])
        test_plans = None
        return top_row, info_row, t_name, m_layout, test_plans

    def issue_layout(db_document: dict, symbol: str) -> list:
        try:
            update_object = db_document.get('update')
            update_date   = update_object.get('lastUpdated')
            update_user   = update_object.get('user')
            document_info = f'--{selected_id} עודכן בתאריך: {update_date.strftime("%d/%m%Y")} על ידי: {update_user}'
        except AttributeError as ex:
            document_info = f'--{selected_id}'

        user_info = [
            selected_row.get('u_name'    ),
            selected_row.get('tn'        ),
            selected_row.get('department'),
            selected_row.get('email'     )
        ]
        o_name = None
        document_info = fa_rendering(text=document_info, symbol=symbol)
        try:
            o_name = db_record.get('full_name')
        except KeyError as ex:
            print('u_name key error in update detail pane', ex)

        x1 = '\n'.join(user_info)
        x2 = db_record.get('subject')
        x3 = db_record.get('note').get('main_note')
        x4 = db_record.get('note').get('secondary_note')
        x5 = db_record.get('owner_notes')[0].get('note')

        x6 = '\n'.join([note.get('note_date') for note in db_record.get('owner_notes')][::-1])
        record_id = 'record id: {}'.format(selected_id)

        subject        = create_md_note(header= h0          , note=x2, oid=record_id)
        main_note      = create_md_note(header= h1          , note=x3, oid=record_id)
        secondary_note = create_md_note(header= h2          , note=x4, oid=record_id)
        owner_date     = create_md_note(header='תאריך עדכון', note=x6, oid=record_id)
        owner_note     = create_md_note(header= 'הערת אחראי', note=x5, oid={'id': record_id, 'date': x6})
        user_object    = create_md_note(header=      'פרטים', note=x1, oid=record_id)

        detail_row = [
            subject,
            main_note,
            secondary_note,
            owner_date,
            owner_note,
            user_object
        ]
        return detail_row, document_info, o_name
    ####################################################################################################################
    update_form_empty   = html.Div()
    input_row           = selected_row
    t_plans             = None
    mtp_layout          = None

    # if ctx.triggered_id == 'task-table' and ctx.inputs.get('task-table.selected_rows'):
    if ctx.inputs.get('task-table.selected_rows'):
        selected_row = rows[selected_row[0]]
        selected_id  = selected_row['_id']
        db_record    = task_db.get_document_by_oid(collection='tasks', oid=selected_id)
        # db_record    = [c for c in db_record][0]
        doctype      = db_record.get('reference').get('doctype')

        h0 = task_types.get(doctype).get('note_headers').get('H0')
        h1 = task_types.get(doctype).get('note_headers').get('H1')
        h2 = task_types.get(doctype).get('note_headers').get('H2')
        match doctype:
            case 'issue':
                doctype_symbol = 'fas fa-book-open fa-lg text-info'
                document_detail_row, record_info, owner_name = issue_layout(
                    db_document=db_record,
                    symbol=doctype_symbol
                )
            case 'test':
                doctype_symbol = 'fas fa-flask fa-lg text-info'
                document_detail_row, record_info, owner_name, mtp_layout, t_plans = testplan_layout(
                    db_document=db_record,
                    symbol=doctype_symbol
                )
            case 'm4n-docx':
                doctype_symbol = 'far fa-edit fa-lg text-info'
                document_detail_row, record_info, owner_name = issue_layout(
                    db_document=db_record,
                    symbol=doctype_symbol
                )
            case _:
                doctype_symbol = 'far fa-edit fa-lg text-info'
                document_detail_row, record_info, owner_name = issue_layout(
                    db_document=db_record,
                    symbol=doctype_symbol
                )
        update_form_by_record_type = update_form(record_type=doctype)

        return document_detail_row, selected_id, owner_name, record_info, input_row, update_form_by_record_type, mtp_layout, t_plans
    return None, '', '', 'no info', [], update_form_empty, update_form_empty, t_plans

@callback(
    Output('owner-notes'     , 'data'         ),
    Input ('owner-date-table', 'selected_rows'),
    State ('owner-notes'     , 'data'         ),
    State ('owner-date-table', 'data'         ),
)
def owner_notes_renderer(selected_row_id, note_rows, date_rows):
    change_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    h1 = 'תאריך עדכון'
    h2 = 'הערת אחראי'
    oid = date_rows[0]['oid'].split(':')[1].strip()
    def select_note_lines(row_id: int):
        selected_date = date_rows[row_id][h1]
        record_db = task_db.get_document_by_oid(collection='tasks', oid=oid)
        owner_notes = record_db.get('owner_notes')
        owner_notes = [note for note in owner_notes]

        owner_depth = len(owner_notes) - 1
        o_index     = owner_depth - row_id
        note_id     = owner_notes[o_index].get('note_id')

        for note in owner_notes:
            if note['note_id'] == note_id:
                note = pd.DataFrame(data=note['note'].split('\n'), columns=[h2])
                note[h2] = note[h2].str.strip()
                mask = note.copy()[h2].astype('bool')
                note = note[mask]

                note_lines = note.to_dict('records')

                return note_lines
        return lines

    if selected_row_id:
        r_id = selected_row_id[0]
        lines = select_note_lines(row_id=r_id)
        return lines
    else:
        r_id = 0
        lines = select_note_lines(row_id=r_id)
        return lines

@callback(
    Output('update-result', 'children'),

    Input('switch-pane'   , 'n_clicks'),
    Input('task-table'    , 'derived_virtual_selected_rows'),
    Input('search-input'  , 'value'   ),
    Input ('update-button', 'n_clicks'),
    Input ('record-id'    , 'data'    ),
    Input ('active-user'  , 'data'    ),
    Input ('owner-name'   , 'data'    ),
    [Input(v_callback, 'value') for v_callback in update_pane_callbacks],
)
def document_update_manager(n_clicks, selected_row, clicks, search, row_id, active_user, owner_name, *args):
    change_id = [p['prop_id'] for p in dash.callback_context.triggered][0].split('.')[0]
    empty = dbc.Alert(f'', color='light', class_name='g-1')
    match change_id:
        case 'update-button':
            full_name = active_user.get('full_name')
            role      = active_user.get('role'     )
            update_document = {
                'priority'  : args[0]   ,
                'sheet'     : args[1]   ,
                'status'    : args[2]   ,
                'due_date'  : args[3]   ,
                'owner_note': args[4]   ,
                'row_id'    : row_id    ,
                'user_name' : full_name ,
                'role'      : role      ,
                'owner_name': owner_name,
            }
            feedback = task_db.update_task_document(u_data=update_document)  # validation happens there
            if feedback:
                message = dbc.Alert(f'successful update'         , color='success', class_name='g-1')
            else:
                message = dbc.Alert(f'update failed, try again'  , color='danger' , class_name='g-1')
            if not isinstance(feedback, bool):
                message = dbc.Alert(f'update failed ->{feedback}', color='danger' , class_name='g-1')
            return message
        case 'task-table':
            return empty
        case 'switch-pane':
            return empty
        case 'search-input':
            return empty
        case _:
            return dash.no_update

@callback(
    Output('clicked-chart', 'data' ),

    Input ('pie-chart', 'clickData'),
    Input ('bar-chart', 'clickData'),
    Input ('pdu-chart', 'clickData'),
)
def parse_chart_event(pie_data, bar_data, pdu_data):
    match ctx.triggered_id:
        case 'pie-chart':
            try:
                selected_label = pie_data.get('points')[0].get('label')
                result = {
                    'chart'    : 'pie',
                    'selection': selected_label
                }
            except AttributeError as ex:
                result = None
        case 'bar-chart':
            selected_label = bar_data.get('points')[0].get('label')
            status         = bar_data.get('points')[0].get('text' )
            result = {
                'chart'    : 'bar',
                'selection': selected_label,
                'status'   : status
            }
        case 'pdu-chart':
            selected_label = pdu_data.get('points')[0].get('label')
            result = {
                'chart'    : 'pdu',
                'selection': selected_label
            }
        case _:
            result = None
    return result

################################### MTP Callbacks ####################################################################
@callback(
    Output('testrun-grid-div' , 'children' ),
    Output('testrun-grid-data', 'data'     ),

    Input('testplan-grid', 'selectedRows'    ),
    State('testplan-grid', 'rowData'         ),
    Input('testplan-grid', 'cellValueChanged'),
)
def testrun_table_creation(selected_row, rows, _):
    # disabled = True if ctx.triggered_id == 'testrun-button' else False
    if selected_row is None:
        return dash.no_update

    ### update test_plan block
    if ctx.inputs.get('testplan-grid.cellValueChanged'):
        test_oid  = ObjectId(_.get('data').get('test_oid'))
        mtp_oid   = ObjectId(_.get('data').get('mtp_oid' ))
        old_value = _.get('old_value')
        new_value = _.get('value'    )
        col_name  = _.get('colId'    )

        db = task_db.get_db()
        result = db.tasks.update_one(
            {'mtp_object.mtp_oid': mtp_oid},
            {
                "$set": {
                    f"mtp_object.test_plan.$[plan].{col_name}": new_value
                }
            },
            array_filters=[
                {'plan.test_oid': test_oid},
            ],
            upsert=True
        )
        print(f'matched: {result.matched_count} modified: {result.modified_count}')
    ### END update block

    row = selected_row[0]
    test_oid = ObjectId(row.get('test_oid'))
    t_steps = pd.DataFrame(get_selected_testplan_data(test_plan_oid=test_oid)[0].get('test_steps'))

    t_steps['mtp_oid' ] = t_steps['mtp_oid' ].astype(str)
    t_steps['test_oid'] = t_steps['test_oid'].astype(str)
    t_steps['step_oid'] = t_steps['step_oid'].astype(str)
    t_steps['bug'     ] = ''
    t_steps['pot'     ] = ''
    t_steps['report'  ] = ''
    ############ AG-GRID ##########################################################################################
    columnDefs             = [
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
              'headerName': "step_oid",
              'field': "step_oid",
              'hide': True,
              'suppressToolPanel': True
          },
          {
              "headerName": "#",
              "field": "step",
              'width': 40,
              'cellClass': 'text-center',
          },
          {
              "headerName": "פעולה",
              "field": "subject",
              'width': 120,
              'cellStyle': {
                  'direction': 'rtl',
                  'white-space': 'normal',
                  'word-break': 'break-word'
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
                  'textAlign': 'right',
                  'direction': 'rtl',
                  'white-space': 'normal',
                  'word-break': 'break-word'
              }
          },
          {
              "headerName": "צילום תקלה",
              "field": "bug",
              'width': 50,
              "cellRenderer": "DBC_Button",
              'cellClass'   : 'text-center',
              "cellRendererParams": {
                  "rightIcon": "fas fa-bug mt-1",
                  "outline"  : True,
                  "color"    : "danger"
              }
          },
          {
              "headerName": "הוכחת בדיקה",
              "field": "pot",
              'width': 50,
              'cellRenderer': "DBC_Button",
              'cellClass'   : 'text-center',
              "cellRendererParams": {
                  "rightIcon": "fas fa-upload mt-1",
                  "outline"  : True,
                  "color"    : "success"
              }
          },
          {
              "headerName": "דיווח תקלה",
              "field": "report",
              'width': 50,
              'cellRenderer': "DBC_Button",
              'cellClass': 'text-center',
              "cellRendererParams": {
                  "rightIcon": "fas fa-file mt-1",
                  "outline": True,
                  "color": "info"
              }
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
    defaultColDef          = {
         # "filter"        : True,
         # "floatingFilter": True,
         "resizable": True,
         "sortable": True,
         "editable": False,
         "minWidth": 20,
         'wrapText': True,
         'autoHeight': True,
         'wrapHeaderText': True,
         'autoHeaderHeight': True,
         "cellStyle": cell_conditional_style,
    }
    ############ AG-GRID END ######################################################################################
    grid = dag.AgGrid(
        id="testrun-grid",
        style={'height': '100%'},
        rowData=t_steps.to_dict("records"),
        className="ag-theme-balham headers1",
        columnDefs=columnDefs,
        columnSize="sizeToFit",
        defaultColDef=defaultColDef,
        dashGridOptions={
             "undoRedoCellEditing": True,
             'enableRtl': True,
             "rowSelection": "single",
             "rowHeight": 48,
             'verticalAlign': 'middle'
        },
    )
    return grid, t_steps.to_dict('records')

@callback(
    Output('moshe-id', 'data'                 ),

    Input ('testrun-grid' , 'cellValueChanged'),
    Input ('testrun-grid' , 'selectedRows'    ),
    State ('testrun-grid' , 'rowData'         ),
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

    db = task_db.get_db()
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

@callback(
    Output('testrun-value-changed'     , 'children'),
    Output("file-handler-modal"        , "is_open" ),
    Output("file-handler-modal-content", "children"),
    Output('step-row-data'             , 'data'    ),

    Input ('testrun-grid'     , 'cellRendererData'),
    Input ('testrun-grid-data', 'data'            ),
    Input ('close'            , 'n_clicks'        ),

)
def step_row_manager(step_row, testrun_data, close_click):  # handles testrun triggers: report and file_load
    def file_handler_layout():
        return html.Div(
            [
                dcc.Upload(
                    id="upload-data",
                    children=html.Div(
                        ["Drag and drop or click to select a file to upload."]
                    ),
                    style={
                        "width"       : "100%",
                        "height"      : "60px",
                        "lineHeight"  : "60px",
                        "borderWidth" : "1px",
                        "borderStyle" : "dashed",
                        "borderRadius": "5px",
                        "textAlign"   : "center",
                        "margin"      : "10px",
                    },
                    multiple=True,
                ),
                html.H2("File List"),
                html.Ul(id="file-list-moshe"),
            ],
            style={"max-width": "500px"},
        )

    if step_row is None:
        return dash.no_update

    if ctx.triggered_id == "close":
        return dash.no_update, False, dash.no_update, dash.no_update

    triggered_column = ctx.triggered[0].get('value').get('colId')
    if ctx.triggered_id == 'testrun-grid' and triggered_column != 'report':
        step_row_data = testrun_data[step_row.get('rowIndex')]
        action = step_row.get('colId')
        step_row_data.update({'action': action})
        if 'actual_result' in step_row_data.keys():
            if step_row_data.get('actual_result') is None:
                return dash.no_update
            else:
                del step_row_data['subject']
                del step_row_data['expected']
                del step_row_data['actual_result']
                del step_row_data['pot']
                del step_row_data['step']
                # return json.dumps(step_row), f'/home/file_handler/{step_row_data}', step_row_data
                return json.dumps(step_row), True, file_handler_layout(), step_row_data
    else:
        return dash.no_update

@callback(
    Output('file-list-moshe'    , 'children'),

    Input ('upload-data'  , 'filename'),
    Input ('upload-data'  , 'contents'),
    Input ('step-row-data', 'data'    )
)
def upload_files_manager(uploaded_filenames, uploaded_file_contents, step_row_data):
    """Save uploaded files and regenerate the file list."""
    action = step_row_data.get('action')
    oid = step_row_data.get('step_oid')
    parent  = sv.UPLOAD_DIRECTORY.joinpath(oid)
    bug_dir = sv.UPLOAD_DIRECTORY.joinpath(parent, 'bug')
    pot_dir = sv.UPLOAD_DIRECTORY.joinpath(parent, 'pot')

    if not parent.exists():
        parent.mkdir()
        bug_dir.mkdir()
        pot_dir.mkdir()

    file_directory = parent.joinpath(action)
    if uploaded_filenames is not None and uploaded_file_contents is not None:
        for name, data in zip(uploaded_filenames, uploaded_file_contents):
            name = f'{round(datetime.datetime.now().timestamp())}-{name}'
            name = file_directory.joinpath(name)
            save_file(name, data)

    files = uploaded_files(file_directory)

    if len(files) == 0:
        return [html.Li("No files yet!")]

    data = []
    for filename in files:
        image_path = file_directory.joinpath(filename).as_posix()
        encoded_image = encode_image(image_path)
        data.append(
            {
                # 'Image': html.Img(src='data:image/png;base64,{}'.format(encoded_image)),
                'Image'   : f'data:image/png;base64,{encoded_image}',
                'Filename': filename
            }
        )

    df = pd.DataFrame(data)
    df.drop_duplicates('Filename', inplace=True)
    columnDefs = [
        {
            "headerName": "Thumbnail",
            "field": "Image",
            "cellRenderer": "ImgThumbnail",
            "width": 85,
        },
        {
            "headerName": "Image Name",
            "field": "Filename",
        },
    ]

    grid = dag.AgGrid(
        id="uploaded-image-grid",
        dashGridOptions={"rowHeight": 100},
        rowData=df.to_dict("records"),
        columnSize="sizeToFit",
        columnDefs=columnDefs,
        style={"height": 475},
    )
    return grid
@callback(
    Output("uploaded-image-div" , "children"        ),
    Input ("uploaded-image-grid", "cellRendererData"),
)
def show_change(data):
    if data:
        return html.Img(
            src=data["value"],
            style={'max-width': 850}
        )
    return None

@callback(
    Output('display-purpose-modal', 'is_open'),

    Input ('display-purpose-modal-button', 'n_clicks'),
    Input ('close-purpose-modal-button'  , 'n_clicks'),
)
def display_purpose_modal(n1, n2):
    if not ctx.triggered_id:
        return dash.no_update

    if ctx.triggered_id == 'display-purpose-modal-button':
        return True

    if ctx.triggered_id == 'close-purpose-modal-button':
        return False

@callback(
    Output('display-bug-report'    , 'is_open'),

    Input('report-bug-button'      , 'n_clicks'),
    Input('close-bug-report-button', 'n_clicks')
)
def bug_report_modal(n1, n2):
    if not ctx.triggered_id:
        return dash.no_update

    if ctx.triggered_id == 'report-bug-button':
        return True

    if ctx.triggered_id == 'close-bug-report-button':
        return False

################################### ***END MTP Callbacks *** ##########################################################
"""
# @callback(
#     Output('test-plans', 'style_data_conditional'       ),
#     Input ('test-plans', 'derived_virtual_selected_rows'),
# )
# def highlight_selected_row(selRows):
#     if selRows is None:
#         return dash.no_update
#     return [
#         {"if": {"filter_query": "{{id}} ={}".format(i)}, "backgroundColor": "#0074D9", 'color': 'whitesmoke'}
#         for i in selRows
#     ]
"""