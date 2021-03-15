# -*- coding: utf-8 -*-

"""Console script for porerefiner."""
import sys, os
import click

from asyncio import run
from pathlib import Path
from functools import wraps, partial

from porerefiner.cli_utils import VALID_RUN_ID, server, hr_formatter, json_formatter, xml_formatter, handle_connection_errors
from porerefiner.samplesheets import load_from_csv, load_from_excel
from porerefiner.protocols.porerefiner.rpc.porerefiner_pb2 import RunRequest, RunListRequest, RunAttachRequest, RunRsyncRequest, TagRequest

# default_config = lambda: os.environ.get('POREREFINER_CONFIG', Path.home() / '.porerefiner' / 'config.yaml')

def default_config():
    path = Path(os.environ.get('POREREFINER_CONFIG', Path.home() / '.porerefiner' / 'config.yaml'))
    if not path.exists():
        path = Path("/etc/porerefiner/config.yaml")
        if not path.exists():
            from porerefiner.config import Config
            socket_path = click.prompt('path to porerefiner server socket?', default=Path('/etc/porerefiner/porerefiner.sock'), show_default=True)
            Config.new_config_file(path, client_only=True, socket_path=socket_path)
    return path



with_config = click.option('--config', default=default_config(), help='Path to PoreRefiner config', show_default=True)

def coroutine(func):
    "Coroutine runner"
    @wraps(func)
    def wrapper(*a, **k):
        return run(func(*a, **k))
    return wrapper

@click.group()
def cli():
    """Command line interface for PoreRefiner, a Nanopore run manager."""
    pass #pragma: no cover


@cli.command()
@handle_connection_errors
@with_config
@click.option('-a', '--all', is_flag=True, default=False, help="Show finished and ongoing runs.")
@click.option('-h', '--human-readable', 'output_format', flag_value=hr_formatter, help='Output in a human-readable table.', default=hr_formatter)
@click.option('-j', '--json', 'output_format', flag_value=json_formatter, help='Output in JSON.')
@click.option('-x', '--xml', 'output_format', flag_value=xml_formatter, help='Output in schemaless XML.')
@click.option('-t', '--tag', 'tags', multiple=True)
@click.option('-e', '--extended', 'extend', default=False, is_flag=True, help="Extended output format.")
@coroutine
async def ps(config, output_format, extend, all=False, tags=[]):
    "Show runs in progress, or every tracked run (--all), or with a particular tag (--tag)."
    with server(config) as serv:
        with output_format(extend) as formatter:
            resp = await serv.GetRuns(RunListRequest(all=all, tags=tags))
            for run in resp.runs.runs:
                formatter(run)

@cli.command()
@handle_connection_errors
@click.option('-h', '--human-readable', 'output_format', flag_value=hr_formatter, help='Output in a human-readable table.', default=hr_formatter)
@click.option('-j', '--json', 'output_format', flag_value=json_formatter, help='Output in JSON.')
@click.option('-x', '--xml', 'output_format', flag_value=xml_formatter, help='Output in schemaless XML.')
@click.argument('run_id', type=VALID_RUN_ID)
@coroutine
async def info(output_format, run_id, config=default_config()):
    "Return information about a run, historical or in progress."
    with server(config) as serv:
        with output_format(extend=True) as formatter:
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

@cli.command()
def template():
    "Write a sample sheet template to STDOUT."
    click.echo("""porerefiner_ver,1.0.1
library_id,
sequencing_kit,
barcode_kits,
sample_id,accession,barcode_id,organism,extraction_kit,comment,user
""")

async def tag_runner(config, run_id, tags=[], untag=False):
    with server(config) as serv:
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
@with_config
@click.argument('run_id', type=VALID_RUN_ID)
@click.argument('tag', type=click.STRING, nargs=-1)
def tag(config, run_id, tag=[]):
    "Add one or more tags to a run."
    run(tag_runner(config, run_id, tag))


@cli.command()
@handle_connection_errors
@with_config
@click.argument('run_id', type=VALID_RUN_ID)
@click.argument('tag', type=click.STRING, nargs=-1)
def untag(config, run_id, tag=[]):
    "Remove one or more tags from a run."
    run(tag_runner(config, run_id, tag, untag=True))

@cli.command()
@handle_connection_errors
@with_config
@click.argument('samplesheet')
@click.option('-r', '--run', 'run_id', type=VALID_RUN_ID, )
@coroutine
async def load(config, samplesheet, run_id=None):
    "Load a sample sheet to be attached to a run, or to the next run that is started."
    try:
        if '.csv' in samplesheet:
            with open(samplesheet, 'r') as file:
                ss = load_from_csv(file)
        elif '.tsv' in samplesheet or '.txt' in samplesheet:
            with open(samplesheet, 'r') as file:
                ss = load_from_csv(file, delimiter='\t')
        elif '.xls' in samplesheet:
            with open(samplesheet, 'rb') as file:
                ss = load_from_excel(file)
    except FileNotFoundError:
        click.echo(f"File '{samplesheet}' not found.")
        return 2
    except ValueError as e:
        click.echo(e, err=True)
    except ImportError:
        click.echo(f"ERROR: OpenPyXL not installed; Excel files ({samplesheet}) can't be read. Use pip to install OpenPyXL.", err=True)
    else:
        with server(config) as serv:
            req = RunAttachRequest(sheet=ss)
            if isinstance(run_id, int):
                req.id = run_id
            elif run_id:
                req.name = run_id
            resp = await serv.AttachSheetToRun(req)
            if resp.error:
                click.echo(resp.error.err_message, err=True)
                return 1
            else:
                click.echo(f"{samplesheet} loaded successfully.")

@cli.command("test-plugins")
@click.argument('config_path', default='/etc/porerefiner/config.yaml')
@coroutine
async def test_plugins(config_path):
    "Suite to test your configured plugins."
    if not Path(config_path).exists():
        raise click.BadParameter(f"No config file at {config_path}.")
    from porerefiner.config import Config
    config = Config(config_path)

    # monkey-patch the subprocess runners plugins usually use
    # so we can intercept output and exit codes

    import subprocess, asyncio
    _run = subprocess.run
    _a_exec = asyncio.create_subprocess_exec
    _a_shell = asyncio.create_subprocess_shell
    def instrumented_run(*args, **kwargs):
        kwargs['capture_output'] = True
        proc = _run(*args, **kwargs)
        click.echo(proc.stdout)
        if proc.returncode: # prompt user if subprocess call failed; for testing purposes they can usually ignore this
            click.echo(proc.stderr)
            if click.confirm("Subprocess ended with non-zero exit code. Ignore failure?"):
                proc.returncode = 0
        return proc
    async def instrumented_exec(_a_sub, *args, **kwargs):
        kwargs['stdout'] = asyncio.subprocess.PIPE
        kwargs['stderr'] = asyncio.subprocess.PIPE
        proc = await _a_sub(*args, **kwargs)
        stdout, stderr = await proc.communicate()
        click.echo(stdout)
        if proc.returncode:
            click.echo(stderr)
            if click.confirm("Subprocess ended with non-zero exit code. Ignore failure?"):
                proc.returncode = 0
        return proc

    subprocess.run = instrumented_run
    asyncio.create_subprocess_exec = partial(instrumented_exec, _a_sub=_a_exec)
    asyncio.create_subprocess_shell = partial(instrumented_exec, _a_sub=_a_shell)

    # Start up the job system with an in-memory database

    from peewee import SqliteDatabase
    from porerefiner import models, jobs, submitters
    db = SqliteDatabase(":memory:", pragmas={'foreign_keys':1}, autoconnect=False)
    db.bind(models.REGISTRY, bind_refs=False, bind_backrefs=False)
    db.connect()
    db.create_tables(models.REGISTRY)

    # Create a fake run

    run = models.Run()

    # Run configured jobs and configured submitters


if __name__ == "__main__":
    sys.exit(cli())  # pragma: no cover