# https://codeburst.io/building-beautiful-command-line-interfaces-with-python-26c7e1bb54df
import click
import os
import yaml
from tabulate import tabulate
from .projector import Projector

DATE_FORMAT = '%Y-%m-%d'


def get_yaml():
    dir_path = os.getcwd()
    with open(f"{dir_path}/balance-projector.yml", "r") as stream:
        return yaml.safe_load(stream)


@click.group()
def cli():
    pass


@cli.command(
    help='Project balances',
    short_help='Project account balances into the future.'
)
@click.option('--account-id', type=click.INT, required=True, help='Account Id to project.')
@click.option('--starting-balance', type=click.FLOAT, required=True, help='Starting balance of the account.')
@click.option('--start-date', type=click.DateTime(formats=[DATE_FORMAT]), required=True, help='Start date.')
@click.option('--end-date', type=click.DateTime(formats=[DATE_FORMAT]), required=True, help='End date.')
def project(account_id, starting_balance, start_date, end_date):
    spec = get_yaml()
    projector = Projector.from_spec(spec)
    df = projector.filter(account_id,
                          start_date.strftime(DATE_FORMAT),
                          end_date.strftime(DATE_FORMAT)
                          )
    df = projector.apply_running_balance(df, starting_balance)
    headers = ['Account ID', 'Date', 'Amount', 'Name', 'Balance']
    click.echo(tabulate(df.to_numpy(), headers=headers))


if __name__ == '__main__':
    cli()
