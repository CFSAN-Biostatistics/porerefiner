# -*- coding: utf-8 -*-

"""Console script for porerefiner."""
import sys
import click

from asyncio import run

from porerefiner.cli_utils import VALID_RUN_ID, server, hr_formatter, json_formatter, xml_formatter
from porerefiner.protocols.porerefiner.rpc.porerefiner_pb2 import RunRequest, RunListRequest, RunAttachRequest, RunRsyncRequest


@click.group()
def cli():
    """Command line interface for PoreRefiner, a Nanopore integration toolkit."""
    pass #doesn't actually need to do anything

@cli.command()
@click.option('-a', '--all', is_flag=True, default=False, help="Show finished and ongoing runs.")
@click.option('-h', '--human-readable', 'output_format', flag_value=hr_formatter, help='Output in a human-readable table.', default=hr_formatter)
@click.option('-j', '--json', 'output_format', flag_value=json_formatter, help='Output in JSON.')
@click.option('-x', '--xml', 'output_format', flag_value=xml_formatter, help='Output in schemaless XML.')
@click.option('-t', '--tag', 'tags', multiple=True)
def ps(output_format, all=False, tags=[]):
    "Show runs in progress, or every tracked run (--all), or with a particular tag (--tag)."
    async def ps_runner(formatter):
        with server() as serv:
            resp = await serv.GetRuns(RunListRequest(all=all, tags=tags))
            for run in resp.runs.runs:
                formatter(run)
    with output_format() as formatter:
        run(ps_runner(formatter=formatter))



# @cli.command()
# @click.argument('run', type=VALID_RUN_ID)
# @click.confirmation_option("Are you sure you want to delete the run?")
# def rm(run):
#     "Remove a run and recover hard drive space."
#     pass

@cli.command()
@click.option('-h', '--human-readable', 'output_format', flag_value=hr_formatter, help='Output in a human-readable table.', default=hr_formatter)
@click.option('-j', '--json', 'output_format', flag_value=json_formatter, help='Output in JSON.')
@click.option('-x', '--xml', 'output_format', flag_value=xml_formatter, help='Output in schemaless XML.')
@click.argument('run', type=VALID_RUN_ID)
def info(output_format, run):
    "Return information about a run, historical or in progress."
    async def info_runner(formatter):
        with server() as serv:
            req = RunRequest()
            if isinstance(run, str):
                req.name = run
            else:
                req.id = run
            resp = await serv.GetRunInfo(req)
            formatter(resp.run, extend=True)
    with output_format() as formatter:
        run(info_runner(formatter))

@cli.command()
def template(): #TODO
    "Write a sample sheet template to STDOUT."
    pass

@cli.command()
@click.argument('samplesheet', type=click.File())
@click.argument('run', type=VALID_RUN_ID)
def load(samplesheet, run=None):
    "Load a sample sheet to be attached to a run, or to the next run that is started."
    async def load_runner():
        rec = RunAttachRequest(file=samplesheet.read())
        if run:
            if isinstance(run, str):
                req.name = run
            else:
                req.id = run
        else:
            with server() as serv:
                #get most recent in-progress run
                resp = await serv.GetRuns(RunListRequest(all=False, tags=[]))
            if not resp.runs:
                raise ValueError("No in-progress runs to attach samples to. Specify a run for this sample sheet.")
            rec.id = resp.runs[0].id
        with server() as serv:
            resp = await serv.AttachSheetToRun(rec)
    run(load_runner())

# @cli.command()
# def proto():
#     "Append to the notifiers section of the config a default config for a new notifier."
#     pass


if __name__ == "__main__":
    sys.exit(cli())  # pragma: no cover
