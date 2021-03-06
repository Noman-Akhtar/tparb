import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from app import app
import monitor


app.layout = html.Div(
    children=[
        dcc.Location(
            id='url',
            refresh=False
        ),
        html.Div(
            id='page-content',
        )
    ]
)


@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
    return monitor.layout


if __name__ == '__main__':
    app.run_server(debug=False)