import dash
import dash_bootstrap_components as dbc
from dash import html

dash.register_page(
    __name__,
    name='Home Page',
    path='/direction-home'
)

layout = dbc.Container(
    [
        html.Div(
            [
                html.Br(),
                dbc.Row(
                    [
                        dbc.Col(),
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardHeader("מערכת ניהול המשימות"),
                                    dbc.CardBody(
                                        [
                                            html.H2("הזדהות למערכת", className="card-title"),
                                            html.P("משתמש עדיין לא מזוהה במערכת", className="card-text"),
                                        ]
                                    ),
                                    dbc.CardFooter(
                                        dbc.Button("כניסה למערכת", href='/', color="primary", class_name='d-block')
                                    ),
                                ],
                                color='secondary',
                                inverse=True,
                                class_name='w-100 card text-center col-3',
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
    ],
    fluid=True
)
