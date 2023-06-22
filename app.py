import os
import dash
import warnings
import dash_bootstrap_components as dbc
import pathlib
import schemas.tm_services as sv
from flask import Flask, send_from_directory
from dash import Dash, dcc, html

task_db = sv.task_db

print('\tAPP has assigned task_db')
warnings.filterwarnings("ignore")
SIDEBAR_STYLE     = {
    'top'             : 0,
    'left'            : 0,
    'bottom'          : 0,
    'width'           : '16rem',
    'padding'         : '2rem 1rem',
    'background-color': '#f8f9fa'
}
navlink_style     = {
    'font-size': 14,
    'border-top': '0,9px solid green'
}
navlink_separator = {
    'font-size': 14,
    'border-top': '3px solid green'
}

app_button = html.Div(
    dbc.Button(
        'כניסה למערכת',
        outline=True,
        color='primary',
        href='/home'
    ), className = 'btn-lg d-grid m-0'
)

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
                className='display-6',
                style={
                    'display': 'inline-block',
                }
            )
        ],
        fluid=True,
        class_name='mt-2 m-0 p-0 display-6',
    )
fa_home = fa_text(text='my home', fa_class='fa-solid fa-chart-gantt ga-md m-2')

sidebar_card = dbc.Card([
        html.H3('my app', className='card-title'),
        dbc.Row(
            [
                dbc.Col(
                    html.Div(
                        html.H6('my_home')
                    ),
                    class_name='mt-0 mb-4'
                )
            ]
        )
    ],
    class_name='card text-center',
    style={
        'border'    : 'none',
        'background': 'none'
    })

siderbar = html.Div([
        sidebar_card,
        dbc.Nav(
            [
                dbc.NavLink(fa_home, href='/home', active='exact', style=navlink_style),
                dbc.NavLink(style=navlink_style)
            ],
            vertical=True,
            pills=True,
            justified=True
        ),
    ])

def page_title() -> dbc.Container:
    return dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        html.A(
                            href='/',
                            className='fa-solid fa-home-lg fa-xl text-warning mt-3',
                        ),
                        class_name='mt-2',
                    ),
                    dbc.Col(
                        dbc.Label(
                            id='logged-user',
                            class_name='text-white mt-2'
                        ),
                        class_name='text-center',
                        style = {'font-size': 18}
                    ),
                    dbc.Col(
                        html.Div(
                            'Welcome to my home'
                        ),
                        class_name='col-8 text-center align-middle fs-2 text-light ',
                    ),
                    dbc.Col(
                        html.Div(
                            [
                                dbc.Button(
                                    id='logout-button',
                                    n_clicks=0,
                                    className='border-0 fa-solid fa-sign-out fa-xl red-color text-warning bg-secondary mt-2',
                                ),
                            ],
                            className='text-start mt-2',
                        ),
                    ),
                ],
                justify='center',
                class_name='bg-secondary'
            )
        ],
        fluid=True
    )

root = pathlib.Path(__file__).parent
try:
    app = Dash(
        __name__,
        assets_folder=root.joinpath('assets').as_posix(),
        use_pages=True,
        prevent_initial_callbacks=True,
        suppress_callback_exceptions=True,
    )
    server = app.server
    app.layout = dbc.Container([
        dcc.Store(id='active-user'),
        dcc.Store(id='record-id'  ),
        dcc.Store(id='owner-name' ),
        dcc.Store(id='step-row-data'),

        dcc.Location(id="url", refresh=True),
        dcc.Location(id="url-1", refresh=True),

        html.Div(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            page_title(),
                            class_name='col-12'
                        ),
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(class_name='col-9'),
                        dbc.Col(
                            html.Div(
                                [
                                    html.Div(id='logout-state'),
                                    html.Span(
                                        id='logout-output',
                                        style={
                                            "verticalAlign": "middle",
                                            'textAlign': 'left'
                                        }
                                    ),
                                ]
                            )
                        )
                    ]
                ),
                dbc.Row(
                    [
                        # dbc.Col(siderbar, class_name='col-1 border-start border-danger'),
                        dbc.Col(
                            dash.page_container,
                            class_name='col-11 border-end border-warning'
                        )
                    ]
                ),
            ],
            lang='he', dir='rtl'
        )
    ],
        fluid=True,
    )
except Exception as ex:
    print(f'\tDash exited: {ex}')

print('\tAPP is about to begin....')
if __name__ == '__main__':
   app.run_server(debug=True)
