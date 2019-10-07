# -*- coding: utf-8 -*-

"""Console script for porerefiner."""
import sys
import click


from .cli_utils import VALID_RUN_ID


@click.group()
def cli():
    """Command line interface for PoreRefiner, a Nanopore integration toolkit."""
    pass #doesn't actually need to do anything

@cli.command()
@click.option('-a', '--all', is_flag=True, default=False, help="Show finished and ongoing runs.")
@click.option('-h', '--human-readable', 'output_format', flag_value='hr', help='Output in a human-readable table.')
@click.option('-j', '--json', 'output_format', flag_value='json', help='Output in JSON.')
@click.option('-x', '--xml', 'output_format', flag_value='xml', help='Output in schemaless XML.')
def ps(output_format, all=False): #TODO
    "Show runs in progress, or every tracked run (--all)."
    pass

@cli.command()
@click.argument('run', type=VALID_RUN_ID)
@click.confirmation_option("Are you sure you want to delete the run?")
def rm(run): #TODO
    "Remove a run and recover hard drive space."
    pass

@cli.command()
@click.argument('run', type=VALID_RUN_ID)
def info(run): #TODO
    "Return information about a run, historical or in progress."
    pass

@cli.command()
def template(): #TODO
    "Write a sample sheet template to STDOUT."
    pass

@cli.command()
@click.argument('samplesheet', type=click.File())
@click.argument('run', type=VALID_RUN_ID)
def load(samplesheet, run=None): #TODO
    "Load a sample sheet to be attached to a run, or to the next run that is started."
    pass

@cli.command()
def proto():
    "Append to the notifiers section of the config a default config for a new notifier."
    pass


if __name__ == "__main__":
    sys.exit(cli())  # pragma: no cover
