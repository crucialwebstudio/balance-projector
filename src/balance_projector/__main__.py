# https://codeburst.io/building-beautiful-command-line-interfaces-with-python-26c7e1bb54df
import click
import os
import yaml
from .projector import Projector


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
@click.option('--start-date', type=click.DateTime(formats=['%Y-%m-%d']), required=True, help='Start date.')
@click.option('--end-date', type=click.DateTime(formats=['%Y-%m-%d']), required=True, help='End date.')
def project(account_id, starting_balance, start_date, end_date):
    spec = get_yaml()
    projector = Projector.from_spec(spec)
    balances = projector.project(account_id, starting_balance,
                                 start_date.strftime('%Y-%m-%d'),
                                 end_date.strftime('%Y-%m-%d'))
    print(balances)


if __name__ == '__main__':
    cli()
