# https://codeburst.io/building-beautiful-command-line-interfaces-with-python-26c7e1bb54df
import click
import os
import yaml


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
@click.option(
    '--account-id',
    type=click.INT,
    required=True,
    help='Account Id to project.'
)
@click.option(
    '--start-date',
    type=click.DateTime(formats=['%Y-%m-%d']),
    required=True,
    help='Start date.'
)
@click.option(
    '--end-date',
    type=click.DateTime(formats=['%Y-%m-%d']),
    required=True,
    help='End date.'
)
def project(account_id, start_date, end_date):
    spec = get_yaml()
    print(spec)


if __name__ == '__main__':
    cli()
