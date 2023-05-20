import dash
import json
import pandas as pd
import dash_bootstrap_components as dbc
import plotly.express as px
import schemas.mongo_schema as ms
from dash import html, dcc, callback, Input, Output, State, ctx
from dash import dash_table as dt
from plotly import graph_objects as go
from typing import Tuple, Any
from schemas import tm_services as sv
from schemas.fields import Priority, SAPDomainEnum, SAPProcessEnum, Status
from schemas.mongo_schema import timing_decorator, dt_date
from devtools import debug

# db.collection.createIndex( { "$**": "text" } )

page_number = 0
task_db     = sv.task_db

dash.register_page(
    __name__,
    name='Home Page',
    path='/home'
)

issue_status = [Status.P_01, Status.P_02, Status.P_03, Status.P_04]
test_status  = [Status.P_10, Status.P_11, Status.P_12]
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

div_hide   = {
    'display': 'none'
}
div_show   = {
    'display': 'block'
}
note_cell_style = {
    'overflow-y': 'scroll',
    'height': 'auto',
    'whiteSpace': 'normal',
    'lineHeight': '15px'
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

priority_values = [{"label": _, "value": _} for _ in Priority.list()      ]
domain_values   = [{"label": _, "value": _} for _ in SAPDomainEnum.list() ]
process_values  = [{"label": _, "value": _} for _ in SAPProcessEnum.list()]
status_values   = [{"label": _, "value": _} for _ in Status.list()        ]

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

######################################################################################################################
def layout():
    return dbc.Container([
        html.Div(
            [
                dcc.Location(id="direction-home", refresh=True),
                dcc.Store(id='filters-query'),
                dcc.Store(id='clicked-chart'),
                dcc.Store(id='previous-dropdowns'),
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
                                id='page-next', type='submit', color='primary',
                                className='fa-solid fa-forward g-2 m-2'
                            ),
                            dbc.Tooltip('next page', target='page-next', placement='bottom'),
                            dbc.Button(
                                id='page-prev', type='submit', color='primary',
                                className='fa-solid fa-backward g-2 m-2'
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
    Input('task-table'  , 'selected_rows'),
)
def pane_manger(selected, clicked: int):
    if ctx.triggered_id == 'task-table' and ctx.inputs.get('task-table.selected_rows'):
        return div_show, div_show, div_show, div_hide
    else:
        return div_hide, div_hide, div_hide, div_show

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
def update_styles(selected_row):
    if selected_row is None:
        return dash.no_update
    else:
        return [
            {
                'if': {
                    'filter_query': '{{id}} = {}'.format(i)
                },
                'backgroundColor': 'midnightblue',
                'color'          : 'whitesmoke',
            }
            for i in selected_row
        ]

@callback(
    Output('users-callback'     , 'options'),
    Output('department-callback', 'options'),
    Output('status-callback'    , 'options'),
    Output('priority-callback'  , 'options'),
    Output('source-callback'    , 'options'),
    Output('wms-domain-callback', 'options'),

    Output('task-table'         , 'data'    ),
    Output('charts-pane'        , 'children'),
    Output('search-feedback'    , 'children'),
    Output('filter-feedback'    , 'children'),
    Output('page-next'          , 'n_clicks'),
    Output('page-prev'          , 'n_clicks'),
    Output('filters-query'      , 'data'    ),
    Output('previous-dropdowns' , 'data'    ),

    Input ('previous-dropdowns' , 'data'    ),
    Input ('filters-query'      , 'data'    ),
    Input ('clicked-chart'      , 'data'    ),
    Input ('page-next'          , 'n_clicks'),
    Input ('page-prev'          , 'n_clicks'),
    Input ('search-input'       , 'value'   ),
    [Input(v_callback, 'value') for v_callback in dropdown_callbacks],
    Input ('switch-pane'        , 'n_clicks'),
    # prevent_initial_call=True
)
@timing_decorator
def main_task_handler(previous_dropdowns, filters_query, clicked_chart, b_next, b_prev, search_input, *args):
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

    display_charts   = html.Div()
    if next_or_prev_selected:   # this is for next and prev pages
        filters_1 = filter_dict.copy()
        df_tasks, documents  = task_db.grand_filter_query(collection='tasks', grand_filter=filters_1, skip=skip)
        dropdown_options     = previous_dropdowns
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
        # if len(df_tasks) > 0 and ctx.triggered_id not in ['page-next', 'page-prev']:
        if len(df_tasks) > 0:
            display_charts = draw_charts(df1=charts_dff, df2=past_due_dff)

    pages        = int(documents/ms.PAGE_SIZE)
    current_page = b_next + 1
    feedback     = dbc.Alert(fa_feedback(page=current_page, pages=pages), color='info', class_name='g-1')

    # empty results
    if len(df_tasks) == 0:
        message = dbc.Alert(f'סליחה, יש לחדש חיפוש לא נמצאו ממצאים', color='danger', class_name='g-1' )
        return [], [], [], [], [], [], None, display_charts, message, feedback, b_next, b_prev, filter_dict, dropdown_options

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
        display_charts, message, feedback, b_next, b_prev, filter_dict, dropdown_options

@callback(
    Output('document-detail-row', 'children'     ),
    Output('record-id'          , 'data'         ),
    Output('owner-name'         , 'data'         ),
    Output('record-info'        , 'children'     ),
    Output('task-table'         , 'selected_rows'),
    Output('update-form'        , 'children'     ),
    Output('test-detail-pane'   , 'children'     ),

    Input ('switch-pane'        , 'n_clicks'     ),
    Input ('task-table'         , 'selected_rows'),
    State ('task-table'         , 'data'         ),
)
def document_detail_pane(switch_pane, selected_row, rows):  # render the update pane only

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

    def render_table(records: list) -> dt.DataTable:
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

    def render_testplans_table(test_plans: list) -> dt.DataTable:
        records = []
        stories = []
        ban = '<i class="fas fa-ban text-danger mt-3"></i>'
        # ban = '<i class="fa fa-cloud" style="color: grey;"></i>'
        for plan in test_plans:
            for t_step in plan.get('test_steps'):
                record = {
                    'step'        : f'{t_step.get("step"):0>2}',
                    'mtp_id'      : t_step.get('test_id'      ),
                    'test_number' : t_step.get('test_number'  ),
                    'exp_sap'     : t_step.get('exp_sap'      ),
                    'exp_wms'     : t_step.get('exp_wms'      ),
                    'status'      : 'status',
                }
                records.append(record)
            story = {
                'mtp_id': plan.get('test_id'),
                'number': plan.get('number'),
                'story' : plan.get('story'),
                # TODO: change prepreq model to string rather than array
                'prereq': 'prereq',
                'tester': plan.get('tester'),
                'result': ban
            }
            stories.append(story)
        dff = pd.DataFrame(stories)
        t_columns = [{'name': i, 'id': i} for i in dff.columns]
        t_columns[5].update({'presentation': 'markdown'})

        table =  dt.DataTable(
            # columns=[{'name': i, 'id': i} for i in dff.columns],
            columns=t_columns,
            data=dff.to_dict('records'),
            hidden_columns=['oid'],
            style_header=header_style,
            style_cell_conditional=note_column_formatting,
            style_cell=note_cell_style,
            style_table={'margin-top': '0px'},
            row_selectable='single',
            markdown_options={"html": True},
            css=[{'selector': '.show-hide', 'rule': 'display: none'}]
        )
        return html.Div(
            table,
            dir='ltr',
            lang='he',
        )

    def test_document_handler(db_document: dict, symbol: str) -> list:
        top_row, info_row, t_name = issue_document_handler(
            db_document=db_document,
            symbol=symbol
        )

        cycle      = db_document.get('reference'  ).get('secret_1'   )
        mtp_id     = db_document.get('test_object').get('test_id'    )
        prod_key   = db_document.get('test_object').get('product_key')
        complexity = db_document.get('test_object').get('complexity' )
        bp_rns     = db_document.get('test_object').get('BP_RN'      )
        chapters   = db_document.get('test_object').get('CDR'        )
        purpose    = db_document.get('test_object').get('purpose'    )
        systems    = db_document.get('test_object').get('systems'    )
        test_plans = db_document.get('test_object').get('test_plan'  )

        first_row = dbc.Row(
            [
                dbc.Col(
                    dbc.Alert(f'Test Cycle: {cycle} MTP ID: {mtp_id}', color='secondary'),
                    class_name='col-12'
                )
            ]
        )
        second_row = dbc.Row(
            [
                dbc.Col(
                    html.Div(render_testplans_table(test_plans=test_plans)),
                    class_name='col-5 mt-0',
                    style=row_style
                ),
                dbc.Col(
                    html.Div(render_table(purpose)),
                    class_name='col-3 mt-0',
                    style=row_style
                ),
                dbc.Col(
                    html.Div(render_table(bp_rns)),
                    class_name='col-2 mt-0',
                    style=row_style
                ),
                dbc.Col(
                    html.Div(render_table(chapters)),
                    class_name='col-1 mt-0',
                    style=row_style
                ),
                dbc.Col(
                    html.Div(render_table(systems)),
                    class_name='col-1 mt-0',
                    style=row_style
                ),
            ],
            justify='center'
        )
        moshe = html.Div(
            [
                first_row,
                second_row
            ]
        )
        return top_row, info_row, t_name, moshe

    def issue_document_handler(db_document: dict, symbol: str) -> list:
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
    document_detail_row = []
    record_info         = html.Div()
    owner_name          = None
    moshe_x             = html.Div()
    if ctx.triggered_id == 'task-table' and ctx.inputs.get('task-table.selected_rows'):
        selected_row = rows[selected_row[0]]
        selected_id  = selected_row['_id']
        db_record    = task_db.get_document_by_oid(collection='tasks', oid=selected_id)
        db_record    = [c for c in db_record][0]
        doctype      = db_record.get('reference').get('doctype')

        h0 = task_types.get(doctype).get('note_headers').get('H0')
        h1 = task_types.get(doctype).get('note_headers').get('H1')
        h2 = task_types.get(doctype).get('note_headers').get('H2')
        match doctype:
            case 'issue':
                doctype_symbol = 'fas fa-file fa-lg text-info'
                document_detail_row, record_info, owner_name = issue_document_handler(
                    db_document=db_record,
                    symbol=doctype_symbol
                )
            case 'test':
                doctype_symbol = 'fas fa-flask fa-lg text-info'
                document_detail_row, record_info, owner_name, moshe_x = test_document_handler(
                    db_document=db_record,
                    symbol=doctype_symbol
                )
            case 'm4n-docx':
                doctype_symbol = 'far fa-edit fa-lg text-info'
                document_detail_row, record_info, owner_name = issue_document_handler(
                    db_document=db_record,
                    symbol=doctype_symbol
                )
            case _:
                doctype_symbol = 'far fa-edit fa-lg text-info'
                document_detail_row, record_info, owner_name = issue_document_handler(
                    db_document=db_record,
                    symbol=doctype_symbol
                )

        update_form_by_record_type = update_form(record_type=doctype)
        return document_detail_row, selected_id, owner_name, record_info, input_row, update_form_by_record_type, moshe_x
    return None, '', '', 'no info', [], update_form_empty, moshe_x

@callback(
    Output('owner-notes'     , 'data'         ),
    Input ('owner-date-table', 'selected_rows'),
    State ('owner-notes'     , 'data'         ),
    State ('owner-date-table', 'data'         ),
)
def manage_owner_note(selected_row_id, note_rows, date_rows):
    change_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    h1 = 'תאריך עדכון'
    h2 = 'הערת אחראי'
    oid = date_rows[0]['oid'].split(':')[1].strip()
    def select_note_lines(row_id: int):
        selected_date = date_rows[row_id][h1]
        record_db = task_db.get_document_by_oid(collection='tasks', oid=oid)
        owner_notes = [note for note in record_db][0].get('owner_notes')

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
def update_document_manager(n_clicks, selected_row, clicks, search, row_id, active_user, owner_name, *args):
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
    Output('clicked-chart', 'data'),

    Input ('pie-chart', 'clickData'),
    Input ('bar-chart', 'clickData'),
    Input ('pdu-chart', 'clickData'),
)
def charts_manager(pie_data, bar_data, pdu_data):
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

# change_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
# ctx_msg = json.dumps({
#     'states'   : ctx.states,
#     'triggered': ctx.triggered,
#     'inputs'   : ctx.inputs
# }, indent=2)
