import logging
from sys import stdout

import click

import analyze
import collect


@click.group(help="YellowDog Virtual Screening", context_settings={'show_default': True})
def cli():
    pass


cli.add_command(analyze.analyze)
cli.add_command(collect.collect)

if __name__ == '__main__':
    logging.basicConfig(stream=stdout, format="[%(levelname)8s] [%(module)17s]: %(message)s", level=logging.INFO)
    cli()
