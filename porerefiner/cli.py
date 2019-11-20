# -*- coding: utf-8 -*-

"""Console script for porerefiner."""
import sys
import click

from asyncio import run

from porerefiner.cli_utils import VALID_RUN_ID, server, hr_formatter, json_formatter, xml_formatter, handle_connection_errors, load_from_csv, load_from_excel
from porerefiner.protocols.porerefiner.rpc.porerefiner_pb2 import RunRequest, RunListRequest, RunAttachRequest, RunRsyncRequest, TagRequest


@click.group()
def cli():
    """Command line interface for PoreRefiner, a Nanopore run manager."""
    pass #pragma: no cover


@cli.command()
@handle_connection_errors
@click.option('-a', '--all', is_flag=True, default=False, help="Show finished and ongoing runs.")
@click.option('-h', '--human-readable', 'output_format', flag_value=hr_formatter, help='Output in a human-readable table.', default=hr_formatter)
@click.option('-j', '--json', 'output_format', flag_value=json_formatter, help='Output in JSON.')
@click.option('-x', '--xml', 'output_format', flag_value=xml_formatter, help='Output in schemaless XML.')
@click.option('-t', '--tag', 'tags', multiple=True)
@click.option('-e', '--extended', 'extend', default=False, is_flag=True, help="Extended output format.")
def ps(output_format, extend, all=False, tags=[]):
    "Show runs in progress, or every tracked run (--all), or with a particular tag (--tag)."
    async def ps_runner(formatter):
        with server() as serv:
            resp = await serv.GetRuns(RunListRequest(all=all, tags=tags))
            for run in resp.runs.runs:
                formatter(run)
    with output_format(extend) as formatter:
        run(ps_runner(formatter=formatter))



# @cli.command()
# @click.argument('run', type=VALID_RUN_ID)
# @click.confirmation_option("Are you sure you want to delete the run?")
# def rm(run):
#     "Remove a run and recover hard drive space."
#     pass

@cli.command()
@handle_connection_errors
@click.option('-h', '--human-readable', 'output_format', flag_value=hr_formatter, help='Output in a human-readable table.', default=hr_formatter)
@click.option('-j', '--json', 'output_format', flag_value=json_formatter, help='Output in JSON.')
@click.option('-x', '--xml', 'output_format', flag_value=xml_formatter, help='Output in schemaless XML.')
@click.argument('run_id', type=VALID_RUN_ID)
def info(output_format, run_id):
    "Return information about a run, historical or in progress."
    async def info_runner(formatter):
        with server() as serv:
            req = RunRequest()
            if isinstance(run_id, str):
                req.name = run_id
            else:
                req.id = run_id
            resp = await serv.GetRunInfo(req)
            if resp.HasField('error'):
                click.echo(f"ERROR: {resp.error.err_message}", err=True)
                quit(1)
            else:
                formatter(resp.run)
    with output_format(extend=True) as formatter:
        run(info_runner(formatter))

@cli.command()
def template():
    "Write a sample sheet template to STDOUT."
    click.echo("""porerefiner_ver,1.0.0
library_id,
sequencing_kit,
sample_id,accession,barcode_id,organism,extraction_kit,comment,user
""")

async def tag_runner(run_id, tags=[], untag=False):
    with server() as serv:
        req = RunRequest()
        if isinstance(run_id, str):
            req.name = run_id
        else:
            req.id = run_id
        resp = await serv.GetRunInfo(req)
        if resp.HasField('error'):
            click.echo(f"ERROR: {resp.error.err_message}", err=True)
            quit(1)
        else:
            run_id = resp.run.id
            return await serv.Tag(TagRequest(id=run_id, tags=tags, untag=untag))

@cli.command()
@handle_connection_errors
@click.argument('run_id', type=VALID_RUN_ID)
@click.argument('tag', type=click.STRING, nargs=-1)
def tag(run_id, tag=[]):
    "Add one or more tags to a run."
    run(tag_runner(run_id, tag, False))


@cli.command()
@handle_connection_errors
@click.argument('run_id', type=VALID_RUN_ID)
@click.argument('tag', type=click.STRING, nargs=-1)
def untag(run_id, tag=[]):
    "Remove one or more tags from a run."
    run(tag_runner(run_id, tag, True))

@cli.command()
@handle_connection_errors
@click.argument('samplesheet', type=click.File())
@click.option('-r', '--run', 'run_id', type=VALID_RUN_ID, )
def load(samplesheet, run_id=None):
    "Load a sample sheet to be attached to a run, or to the next run that is started."
    try:
        if 'csv' in samplesheet.name:
            ss = load_from_csv(samplesheet)
        elif 'tsv' in samplesheet.name or 'txt' in samplesheet.name:
            ss = load_from_csv(samplesheet, delimiter='\t')
        elif 'xls' in samplesheet.name:
            ss = load_from_excel(samplesheet)
    except TypeError:
        click.echo("ERROR: File in bad format or has missing fields.", err=True)
    except ImportError:
        click.echo(f"ERROR: OpenPyXL not installed; Excel files ({samplesheet.name}) can't be read. Use pip to install OpenPyXL.", err=True)
    else:
        async def load_runner(run_id, message):
            with server() as serv:
                if not run_id: #TODO
                    # find first unassociated run
                    run_id = 1
                req = RunAttachRequest(sheet=message)
                if isinstance(run_id, int):
                    req.id = run_id
                else:
                    req.name = run_id
                resp = await serv.AttachSheetToRun(req)
                if resp.error:
                    click.echo(resp.error.err_message, err=True)
                    quit(1)
        run(load_runner(run_id, ss))



# @cli.command()
# def proto():
#     "Append to the notifiers section of the config a default config for a new notifier."
#     pass


if __name__ == "__main__":
    sys.exit(cli())  # pragma: no cover
