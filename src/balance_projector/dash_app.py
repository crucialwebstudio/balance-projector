from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html

DATE_FORMAT = '%Y-%m-%d'


def create_app(trans_group_df):
    chart = go.Figure()
    chart.update_layout(title='Balance over time')
    chart.add_trace(
        go.Scatter(
            name='Checking Account',
            x=trans_group_df.index, y=trans_group_df['balance'].round(0),
            mode='lines+markers',
            line_shape='spline',
            hovertext=trans_group_df['amt_desc'],
            hovertemplate=
            '<b>$%{y:.2f}</b> (%{x})<br><br>' +
            '%{hovertext}'
        )
    )

    headers = ['date']
    headers.extend(list(trans_group_df.columns))
    table = go.Figure(data=[go.Table(
        header=dict(values=headers, align='left', fill_color='paleturquoise'),
        cells=dict(values=[trans_group_df.index, trans_group_df.amt_desc, trans_group_df.amount, trans_group_df.balance], align='left', fill_color='lavender')
    )])
    table.update_layout(title='Checking Account')

    # fig = px.line(df, x=df.index, y=df['balance'].round(0),
    #               hover_name=df['balance'].round(0),
    #               hover_data={
    #                   'date': df.index,
    #                   'desc': df['amt_desc']
    #               },
    #               title='Checking Account',
    #               markers=True)
    app = Dash(__name__)
    app.layout = html.Div(
        children=[
            html.H1(children="Balance Projector", ),
            html.P(
                children="Project your future account"
                         " balances based on a specification file.",
            ),
            dcc.Graph(
                figure=chart,
            ),
            dcc.Graph(
                figure=table,
            ),
        ]
    )

    return app
