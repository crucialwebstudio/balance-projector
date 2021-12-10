from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html

DATE_FORMAT = '%Y-%m-%d'


def create_app(*charts):
    children = []
    for chart in charts:
        if chart.type == 'line':
            fig = go.Figure()
            fig.update_layout(title=chart.name)
            for account in chart.accounts:
                transactions_df = account['df']
                fig.add_trace(
                    go.Scatter(
                        name=account['name'],
                        x=transactions_df.index, y=transactions_df['balance'].round(0),
                        mode='lines+markers',
                        line_shape='spline',
                        hovertext=transactions_df['amt_desc'],
                        hovertemplate=
                        '<b>$%{y:.2f}</b> (%{x})<br><br>' +
                        '%{hovertext}'
                    )
                )
            children.append(dcc.Graph(figure=fig))

        if chart.type == 'table':
            for account in chart.accounts:
                transactions_df = account['df']
                headers = ['date']
                headers.extend(list(transactions_df.columns))
                fig = go.Figure(data=[go.Table(
                    header=dict(values=headers, align='left', fill_color='paleturquoise'),
                    cells=dict(values=[transactions_df.index, transactions_df.amt_desc, transactions_df.amount,
                                       transactions_df.balance], align='left', fill_color='lavender')
                )])
                fig.update_layout(title=account['name'])
                children.append(dcc.Graph(figure=fig))

    app = Dash(__name__)
    app.layout = html.Div(
        children=[
            html.H1(children="Balance Projector", ),
            html.P(
                children="Project your future account"
                         " balances based on a specification file.",
            ),
            html.Div(children=children)
        ]
    )

    return app
