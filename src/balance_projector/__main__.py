# https://codeburst.io/building-beautiful-command-line-interfaces-with-python-26c7e1bb54df
import click


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
    print('hello')


if __name__ == '__main__':
    cli()
