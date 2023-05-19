import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, register_page, Input, Output, State, callback
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from typing import Dict
from pydantic import ValidationError

import schemas.tm_services as sv
from schemas.fields import LoginModel, Department
from devtools import debug

department_values = [{"label": _, "value": _} for _ in Department.list()]
task_db = sv.task_db

register_page(
    __name__,
    path="/"
)
card_icon    = {
    'margin-top': 0,
    'margin-left': 12,
    'display': 'inline-block'
}
input1_style = {
    'height'      : '45px',
    'padding'     : '10px',
    'margin-top'  : '25',
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
    fa_class='fa-regular fa-sign-in fa-md m-2',
    text='כניסה'
)

register_fields = html.Div([
        dbc.Input(
            id="full-name",
            type="text",
            placeholder="שם מלא",
            debounce=True,
            maxLength=15,
            size='md',
            class_name='mb-3 border border-secondary text-secondary',
        ),
        dbc.Select(
            id="department",
            placeholder="מחלקה",
            size='md',
            class_name='mb-3 border border-secondary text-secondary',
            options=department_values
        ),
        dbc.Input(
            id="telephone",
            type="text",
            placeholder="טלפון xxx-xxx-xxxx",
            debounce=True,
            maxLength=15,
            size='md',
            class_name='mb-3 border border-secondary text-secondary',
        ),
        dbc.Input(
            id="username",
            type="text",
            placeholder="קוד משתמש",
            debounce=True,
            maxLength=15,
            size='md',
            class_name='mb-3 border border-secondary text-secondary',
        ),
        dbc.Input(
            id="password",
            type="password",
            debounce=True,
            placeholder="סיסמא",
            class_name='mb-3 border border-secondary text-secondary',
            size='md',
        ),
        dbc.Input(
            id="v-password",
            type="password",
            debounce=True,
            placeholder="אימות סיסמא ...",
            size='md',
            class_name='mb-3 border border-secondary text-secondary',
        ),
        dbc.Input(
            id="email",
            type="email",
            debounce=True,
            placeholder="כתובת מייל",
            maxLength=50,
            size='md',
            class_name='mb-3 border border-secondary text-secondary',
        ),
    ]
)
register_header = html.Div([
        html.H6(
            title_01,
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
register_footer = html.Div([
        dbc.Button(
            'Create User',
            id='submit-val',
            n_clicks=0,
            outline=True,
            color='info',
            class_name='fs-3'
        ),
        html.Div(id='output-message')
    ], className='btn-lg d-grid m-0'
)
login_header    = html.Div([
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
login_fields    = html.Div([
        dbc.Input(
            placeholder='שם משתמש רשום',
            debounce=True,
            type='text',
            id='uname-box',
            size='md',
            class_name='mb-3',
            style=input1_style
        ),
        dbc.Input(
            placeholder='סיסמא',
            type='password',
            debounce=True,
            id='pwd-box',
            style=input2_style,
            size='md',
            class_name='mb-3'
        ),
        html.Div(id='output-state'),
    ]
)
app_button = dbc.Button(
    'Click to enter app',
    type='button',
    href='/home',
    color='dark',
    class_name='fs-4 btn-lg m-3'
)
login_footer    = html.Div([
        html.Div(
            dbc.Button(
                'Please Login',
                id='login-button',
                n_clicks=0,
                outline=True,
                color='info',
                class_name='fs-4 btn-lg m-3'
            ),
            className='d-grid'
        ),
        html.Div(
            dcc.Loading(
                [
                    html.Div(id='login-roll'   ),
                    html.Div(
                        id='go-app',
                        className='d-grid'
                    ),
                ],
                type='dot'
            )
        ),
        html.Hr(),
        dcc.Link('reset password', href='/pw-reset', className='text-center text-muted my-2'),
], className='d-grid m-0'
)


landing_page = dbc.Row([
        dbc.Col(
            sv.display_card(
                header=login_header,
                body  =login_fields,
                footer=login_footer,
            ),
            class_name='col-3'
        ),
        dbc.Col(
            class_name='col-1'
        ),
        dbc.Col(
            sv.display_card(
                header=register_header,
                body  =register_fields,
                footer=register_footer,
            ),
            class_name='col-3'
        ),
    ],
    justify='center'
)

layout = dbc.Container([
        html.Div(
            [landing_page],
        )
    ], fluid=True
)
@callback(
    Output('output-message', "children"),
    Output('department'    , 'value'),
    Output('telephone'     , 'value'),
    Output('username'      , 'value'),
    Output('password'      , 'value'),
    Output('v-password'    , 'value'),
    Output('email'         , 'value'),

    Input ('submit-val'    , 'n_clicks'),
    Input ('full-name'     , 'value'   ),
    State ('department'    , 'value'   ),
    State ('telephone'     , 'value'   ),
    State ('username'      , 'value'   ),
    State ('password'      , 'value'   ),
    State ('v-password'    , 'value'   ),
    State ('email'         , 'value'   )
)
def insert_users(n_clicks, fn, dep, tn, un, pw, v_pw, em):
    def value_from_validation_error(d: Dict, ex: ValidationError):
        for error in ex.errors():
            loc = list(error["loc"])[0]
            msg = error['msg']
            return f'{loc} {msg}'
    def message(text: str, color: str) -> dbc.Label:
        return dbc.Label(text, color=color, class_name='text-start')

    record = {}
    change_id = [p['prop_id'] for p in dash.callback_context.triggered][0].split('.')[0]
    if change_id is None:
        return dash.no_update

    if change_id == 'full-name':
        record = task_db.get_document_by_field(collection='user', field='full_name', value=fn)
        c = [c for c in record]
        if len(c) == 0:
            return message(text='user name is not eligible, please contact Eithan 052-212-1230', color='danger'), '', '', '', '', '', ''
        else:
            c = c[0]
            v_fn  = c.get('full_name')
            v_dep = c.get('department')
            v_tn  = c.get('telephone')
            v_em  = c.get('email')
            return '', v_dep, v_tn, '',  '', '', v_em

    if un is not None and pw is not None and em is not None:
        hashed_password = generate_password_hash(pw, method='sha256')
        user_record = {}
        try:
            user_record = LoginModel.parse_obj(
                {
                    'full_name' : fn,
                    'department': dep,
                    'tn'        : '+972' + tn,
                    'username'  : un,
                    'email'     : em,
                    'password'  : pw,
                    'v_password': v_pw,
                    'signup_ts' : datetime.now()
                }
            ).dict()
        except ValidationError as ex:
            msg = value_from_validation_error(d=user_record, ex=ex)
            return message(text=msg, color='danger'), dep, tn, '', '', '', em
        cursor = task_db.get_document_by_field(collection='user', field='full_name', value=fn)
        user = [c for c in cursor][0]
        if user.get('u_id') and user.get('u_id') == un:
            return message(text='user already exist', color='danger'), '', '', '', '', '', ''
        else:
            record = task_db.get_document_by_field(collection='user', field='full_name', value=fn)
            query = [c for c in record][0]
            oid = str(query.pop('_id'))
            query.update(
                {
                    'full_name' : fn,
                    'department': dep,
                    'telephone' : user_record.get('tn'),
                    'u_id'      : un,
                    'email'     : em,
                    'password'  : hashed_password,
                    'signup_ts' : datetime.now()
                }
            )
            if task_db.update_field_by_oid(collection='user', query=query, oid=oid):
                return message(text='successful registration... please login', color='success'), '', '', '', '', '', ''
            else:
                return message(text='update failed please call 052-212-1230' , color='danger' ), '', '', '', '', '', ''
    else:
        return  dash.no_update

@callback(
    Output('login-roll', 'children'     ),
    Input ('task-table', 'loading_state')
)
def on_loading(state):
    return


@callback(
    Output('output-state', 'children'),
    Output('logged-user' , 'children'),
    Output('active-user' , 'data'    ),
    Output('go-app'      , 'children'),

    Input ('login-button', 'n_clicks'),
    State ('uname-box'   , 'value'   ),
    State ('pwd-box'     , 'value'   ),
)
def login_callback(n_clicks, input1, input2):
    full_name = None
    au = {
        'full_name': None,
        'role'     : None
    }
    if n_clicks > 0 and input1 and input2:
        cursor = task_db.get_document_by_field(collection='user', field='u_id', value=input1)
        user   = [c for c in cursor][0]
        if not user:
            return dbc.Label('user does not exist', color='danger'), full_name, '', None

        password_hash = user.get('password')
        if user:
            if check_password_hash(password_hash, input2):
                full_name = user.get('full_name')
                session = {
                    'u_uid'     : input1,
                    'action'    : 'login',
                    'timestamp' : datetime.now()
                }
                task_db.insert_one_document(collection='session', record=session)
                au = {
                    'full_name': full_name,
                    'role'     : user.get('role')
                }
                return None, full_name, au, app_button
            else:
                return dbc.Label('login failed', color='danger'), full_name, au, None
        else:
            return dbc.Label('login failed', color='danger'), full_name, au, None
    else:
        return dash.no_update

@callback(
    Output('url'          , 'href'    ),
    Input ('logout-button', 'n_clicks'),
    config_prevent_initial_callbacks=True
)
def logout_callback(n):
    change_id = [p['prop_id'] for p in dash.callback_context.triggered][0].split('.')[0]
    print(change_id, n)
    if n is None:
        return dash.no_update
    else:
        return '/direction-home'
