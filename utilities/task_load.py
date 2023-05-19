moshe = [
    {
        'if': {'column_id': c},
        'textAlign': 'left',
        'backgroundColor': 'rgb(240, 240, 240)',
        'border': '1px solid rgb(0, 116, 217)',
        'width': '10%',
        'padding': '3px'
    } for c in ['a', 'b']
]

moshe.append(
        {
            'if'             : {'column_id': 'row_number'},
            'backgroundColor': 'rgb(231, 235, 224)',
            'border'         : '1px solid rgb(0, 116, 217)',
            'width'          : '5%',
            'textAlign'      : 'center',
            'verticalAlign'  : 'middle',
            'padding'        : '3px',
        }
)

x = 1

import dash_bootstrap_components as dbc
from dash import html
import dash

body = dbc.Container(
    [
        dbc.Row(
            [
                html.H1("test")
            ],
            justify="center",
            align="center",
            className="h-50"
        )
    ],
    style={"height": "100vh"}
)

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.SUPERHERO]
)

app.layout = html.Div(
    [body]
)

if __name__ == "__main__":
    app.run_server(debug=True)