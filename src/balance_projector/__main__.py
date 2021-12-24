# https://codeburst.io/building-beautiful-command-line-interfaces-with-python-26c7e1bb54df
import os
from datetime import date
from dateutil.relativedelta import relativedelta
import click
import yaml
from .projector import Projector, DATE_FORMAT
from .dash_app import create_app


def get_yaml():
    dir_path = os.getcwd()
    dist_file = f"{dir_path}/balance-projector.dist.yml"
    user_file = f"{dir_path}/balance-projector.yml"
    spec_file = user_file if os.path.exists(user_file) else dist_file
    with open(spec_file, "r") as stream:
        return yaml.safe_load(stream)


@click.group()
def cli():
    pass


@cli.command(help='Run the dash app')
@click.option('--start-date', type=click.DateTime(formats=[DATE_FORMAT]), required=True,
              default=str(date.today()), help='Start date.')
@click.option('--end-date', type=click.DateTime(formats=[DATE_FORMAT]), required=True,
              default=str(date.today() + relativedelta(years=1)), help='End date.')
def dash(start_date, end_date):
    spec = get_yaml()
    projector = Projector.from_spec(spec,
                                    start_date.strftime(DATE_FORMAT),
                                    end_date.strftime(DATE_FORMAT))
    charts = projector.get_charts()
    app = create_app(*charts)
    app.run_server(debug=True)


if __name__ == '__main__':
    cli()
