import base64
import os
import dash
import datetime
import pathlib
import dash_bootstrap_components as dbc
import schemas.tm_services as sv
from urllib.parse import quote as urlquote
from dash import html, dcc, register_page, Input, Output, State, callback
from schemas.fields import ResetLoginModel, Department
from urllib.parse import unquote
from devtools import debug
from bson import ObjectId

register_page(
    __name__,
    path='/home/file_handler',
    path_template='/home/file_handler<step_row>',
)

def layout(step_row=None, **other_unknown_query_strings):
    step_row = unquote(step_row)
    step_row = step_row.replace('/', '')
    step_record = eval(step_row)

    return html.Div(
        [
            html.H1("File Browser"),
            html.H2("Upload"),
            dcc.Upload(
                id="upload-data",
                children=html.Div(
                    ["Drag and drop or click to select a file to upload."]
                ),
                style={
                    "width": "100%",
                    "height": "60px",
                    "lineHeight": "60px",
                    "borderWidth": "1px",
                    "borderStyle": "dashed",
                    "borderRadius": "5px",
                    "textAlign": "center",
                    "margin": "10px",
                },
                multiple=True,
            ),
            html.H2("File List"),
            html.Ul(id="file-list"),
            dbc.Button(
                'back',
                id='moshe',
                href='/home'
            )
        ],
        style={"max-width": "500px"},
    )


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
        if os.path.isfile(filename):
            files.append(filename)
        else:
            print('moshe')
    return files


def file_download_link(filename, file_directory):
    """Create a Plotly Dash 'A' element that downloads a file from the app."""

    location = "/download/{}".format(urlquote(filename))
    location = file_directory.joinpath(filename).as_posix()
    return html.A(filename, href=location)


@callback(
    Output('file-list'     , 'children'),

    Input ('upload-data'   , 'filename'),
    Input ('upload-data'   , 'contents'),
    Input('step-row-data'  , 'data'    )
)
def update_output(uploaded_filenames, uploaded_file_contents, step_row_data):
    """Save uploaded files and regenerate the file list."""
    action = step_row_data.get('action')
    oid = step_row_data.get('step_oid')
    parent = sv.UPLOAD_DIRECTORY.joinpath(oid)
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
    else:
        return [
            html.Li(
                file_download_link(filename, file_directory)
            ) for filename in files
        ]

