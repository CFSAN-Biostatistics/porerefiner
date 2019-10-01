# -*- coding: utf-8 -*-

"""Console script for porerefiner."""
import sys
import click


from .cli_utils import ValidRunID


@click.group()
def cli():
    """Console script for porerefiner."""
    pass #doesn't actually need to do anything

@cli.command()
def ps(e=False): #TODO
    "Show runs in progress, or every tracked run"
    pass

@cli.command()
@click.argument('run', type=cli_utils.ValidRunID)
def rm(run): #TODO
    "Remove a run and recover hard drive space"
    pass

@cli.command()
@click.argument('run', type=cli_utils.ValidRunID)
def info(run): #TODO
    "Return information about a run, historical or in progress"
    pass

@cli.command()
def template(): #TODO
    "Write a sample sheet template to STDOUT"
    pass

@cli.command()
@click.argument('samplesheet', type=click.File)
@click.argument('run', type=ValidRunID)
def load(samplesheet, run=None): #TODO
    "Load a sample sheet to be attached to a run, or to the next run that is started"
    pass



if __name__ == "__main__":
    sys.exit(cli())  # pragma: no cover
