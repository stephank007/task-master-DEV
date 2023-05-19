import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, register_page, Input, Output, State, callback
from werkzeug.security import generate_password_hash
from datetime import datetime
from typing import Dict
from pydantic import ValidationError
import schemas.tm_services as sv
from schemas.fields import ResetLoginModel, Department
from devtools import debug

department_values = [{"label": _, "value": _} for _ in Department.list()]
task_db = sv.task_db

register_page(
    __name__,
    path="/pw-reset"
)

card_icon    = {
    'margin-top': 0,
    'margin-left': 12,
    'display': 'inline-block'
}
input1_style = {
    'height'      : '45px',
    'padding'     : '10px',
    'margin-top'  : '35',
    'font-size'   : '16px',
    'border-width': '2px',
    'border-color': '#a0a3a2'
}
input2_style = {
    'height'      : '45px',
    'padding'     : '10px',
    'margin-top'  : '10px',
    'font-size'   : '16px',
    'border-width': '2px',
    'border-color': '#a0a3a2',
}
input3_style = {
    'height'      : '45px',
    'padding'     : '10px',
    'margin-top'  : '10px',
    'margin-bottom'  : '25px',
    'font-size'   : '16px',
    'border-width': '2px',
    'border-color': '#a0a3a2'
}
input4_style = {
    'height'       : '45px',
    'padding'      : '10px',
    'padding-right': '35px',
    'margin-top'   : '10px',
    'margin-bottom': '25px',
    'font-size'    : '16px',
    'border-width' : '2px',
    'border-color' : '#a0a3a2',
    'color': 'rgb(110, 117, 124)'
}
title_01 = sv.fa_text(
    fa_class='fa-regular fa-tasks fa-md m-2',
    text='הרשמה'
)
title_02 = sv.fa_text(
    fa_class='fa-regular fa-key fa-md m-2',
    text='איפוס סיסמא'
)

reset_header    = html.Div([
    html.H6(
        title_02,
        className='card-title display-5',
        style={
            'textAlign'     : 'center',
            'color'         : 'darkblue',
            'border'        : 'none',
            'display'       : 'inline-block',
            'vertical-align': 'center'
        }
    )
]
)
reset_fields    =  html.Div([
    dbc.Input(
        placeholder='שם משתמש רשום',
        debounce=True,
        type='text',
        id='reset-username',
        size='md',
        style=input1_style,

    ),
    dbc.Input(
        placeholder='סיסמא',
        type='password',
        debounce=True,
        id='reset-password',
        style=input2_style,
        size='md',
    ),
    dbc.Input(
        id="reset-v-password",
        type="password",
        debounce=True,
        placeholder="אימות סיסמא ...",
        size='md',
        style=input2_style,
        class_name='border border-secondary text-secondary',
    ),
    html.Div(id='output-state'),
]
)
reset_footer = html.Div([
    dbc.Button(
        'Reset Password',
        id='reset-button',
        n_clicks=0,
        outline=True,
        color='dark',
        class_name='my-3 fs-3'
    ),
    dcc.Link('', href='/', className='text-center text-muted mt-3 fas fa-home fa-lg m-3'),
], className='btn-lg d-grid'
)
landing_page = dbc.Row([
        dbc.Col(
            sv.display_card(
                header=reset_header,
                body  =reset_fields,
                footer=reset_footer,
            ),
            class_name='col-3'
        ),
    ],
    justify='center'
)

layout = dbc.Container([html.Div(
    [
        html.Br(),
        dbc.Row(
            [
                dbc.Col(),
                dbc.Col(
                    dbc.Card(
                        [
                            reset_header,
                            reset_fields,
                            html.Div(id='feedback-message'),
                            reset_footer
                        ],
                        color='white',
                        inverse=True,
                        class_name='border border-info border-3 w-100 card text-center col-3',
                    ),
                ),
                dbc.Col(),
            ],
            justify='center',
            align='center',
            style={"height": "50vh"},
        ),
    ],
)
], fluid=True)

@callback(
    Output('feedback-message', 'children'),

    Input ('reset-button'    , 'n_clicks'),
    State ('reset-username'  , 'value'   ),
    State ('reset-password'  , 'value'   ),
    State ('reset-v-password', 'value'   ),
)
def insert_users(n_clicks, un, pw, v_pw):
    def value_from_validation_error(d: Dict, ex: ValidationError):
        for error in ex.errors():
            loc = list(error["loc"])[0]
            msg = error['msg']
            return f'{loc} {msg}'
    def message(text: str, color: str) -> dbc.Label:
        output_message = dbc.Label(
            text,
            color=color
        )
        return output_message

    record = {}
    oid = None
    change_id = [p['prop_id'] for p in dash.callback_context.triggered][0].split('.')[0]
    if change_id is None:
        return dash.no_update

    query = {'u_id': un}
    cursor = task_db.get_documents_by_query(collection='user', query=query)
    result = [c for c in cursor]
    if not result:
        return message(text=f'user {un} was not found', color='danger')
    else:
        oid = str(result[0].get('_id'))

    if un is not None and pw is not None and v_pw is not None:
        hashed_password = generate_password_hash(pw, method='sha256')
        user_record = {}
        try:
            user_record = ResetLoginModel.parse_obj(
                {
                    'password'  : pw,
                    'v_password': v_pw,
                }
            ).dict()
        except ValidationError as ex:
            msg = value_from_validation_error(d=user_record, ex=ex)
            return message(text=msg, color='danger')
        if task_db.update_field_by_oid(collection='user', query={'password': hashed_password}, oid=oid):
            return message(text='successful password reset', color='success')
        else:
            return message(text='reset failed, try again', color='danger')

    else:
        return  dash.no_update
