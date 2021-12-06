# https://codeburst.io/building-beautiful-command-line-interfaces-with-python-26c7e1bb54df
import os
from datetime import date
from dateutil.relativedelta import relativedelta
import click
import yaml
from tabulate import tabulate
from .projector import Projector
from .dash_app import create_app

DATE_FORMAT = '%Y-%m-%d'


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
    start_str = start_date.strftime(DATE_FORMAT)
    end_str = end_date.strftime(DATE_FORMAT)
    spec = get_yaml()
    projector = Projector.from_spec(spec)
    df = projector.get_running_balance(account_id,
                                       start_str,
                                       end_str
                                       )
    headers = ['Account ID', 'Date', 'Amount', 'Name', 'Balance']
    click.echo(tabulate(df.to_numpy(), headers=headers))


@cli.command(help='Run the dash app')
@click.option('--account-id', type=click.INT, required=True, help='Account Id to project.')
@click.option('--starting-balance', type=click.FLOAT, required=True, help='Starting balance of the account.')
@click.option('--start-date', type=click.DateTime(formats=[DATE_FORMAT]), required=True, help='Start date.')
@click.option('--end-date', type=click.DateTime(formats=[DATE_FORMAT]), required=True, help='End date.')
def dash(account_id, starting_balance, start_date, end_date):
    spec = get_yaml()
    projector = Projector.from_spec(spec)

    df = projector.filter(account_id, start_date.strftime(DATE_FORMAT), end_date.strftime(DATE_FORMAT))
    df = projector.group_by_date(df)
    df = projector.apply_running_balance(df, starting_balance)

    app = create_app(df)
    app.run_server(debug=True)


if __name__ == '__main__':
    cli()
