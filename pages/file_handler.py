import base64
import os
import dash
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
    debug(step_record)

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
        ],
        style={"max-width": "500px"},
    )


def save_file(name, content):
    """Decode and store a file uploaded with Plotly Dash."""
    data = content.encode("utf8").split(b";base64,")[1]
    file_name = sv.UPLOAD_DIRECTORY.joinpath(f'moshe-xyz-{name}').as_posix()
    print(file_name)
    with open(file_name, "wb") as fp:
        fp.write(base64.decodebytes(data))


def uploaded_files():
    """List the files in the upload directory."""
    files = []
    for filename in os.listdir(sv.UPLOAD_DIRECTORY):
        path = os.path.join(sv.UPLOAD_DIRECTORY, filename)
        if os.path.isfile(path):
            files.append(filename)
    return files


def file_download_link(filename):
    """Create a Plotly Dash 'A' element that downloads a file from the app."""
    location = "/download/{}".format(urlquote(filename))
    return html.A(filename, href=location)


@callback(
    Output('file-list'  , 'children'),

    Input ('upload-data', 'filename'),
    Input ('upload-data', 'contents'),
)
def update_output(uploaded_filenames, uploaded_file_contents):
    """Save uploaded files and regenerate the file list."""

    if uploaded_filenames is not None and uploaded_file_contents is not None:
        for name, data in zip(uploaded_filenames, uploaded_file_contents):
            save_file(name, data)

    files = uploaded_files()
    if len(files) == 0:
        return [html.Li("No files yet!")]
    else:
        return [
            html.Li(
                file_download_link(filename)
            ) for filename in files
        ]

