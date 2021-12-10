# https://codeburst.io/building-beautiful-command-line-interfaces-with-python-26c7e1bb54df
import os
from datetime import date
from dateutil.relativedelta import relativedelta
import click
import yaml
from tabulate import tabulate
from .projector import Projector, DATE_FORMAT
from .dash_app import create_app


def get_yaml():
    dir_path = os.getcwd()
    with open(f"{dir_path}/balance-projector.yml", "r") as stream:
        return yaml.safe_load(stream)


@click.group()
def cli():
    pass


@cli.command(help='Print running balance')
@click.option('--account-id', type=click.INT, required=True, help='Account Id to project.')
@click.option('--start-date', type=click.DateTime(formats=[DATE_FORMAT]), required=True,
              default=str(date.today()), help='Start date.')
@click.option('--end-date', type=click.DateTime(formats=[DATE_FORMAT]), required=True,
              default=str(date.today() + relativedelta(years=1)), help='End date.')
def project(account_id, start_date, end_date):
    spec = get_yaml()
    projector = Projector.from_spec(spec)
    account = projector.get_account(account_id)
    df = account.get_running_balance(start_date.strftime(DATE_FORMAT), end_date.strftime(DATE_FORMAT))
    headers = ['Account ID', 'Date', 'Amount', 'Name', 'Balance']
    click.echo(tabulate(df.to_numpy(), headers=headers))


@cli.command(help='Run the dash app')
@click.option('--start-date', type=click.DateTime(formats=[DATE_FORMAT]), required=True,
              default=str(date.today()), help='Start date.')
@click.option('--end-date', type=click.DateTime(formats=[DATE_FORMAT]), required=True,
              default=str(date.today() + relativedelta(years=1)), help='End date.')
def dash(start_date, end_date):
    spec = get_yaml()
    projector = Projector.from_spec(spec)
    charts = projector.get_charts(start_date, end_date)
    app = create_app(*charts)
    app.run_server(debug=True)


if __name__ == '__main__':
    cli()
