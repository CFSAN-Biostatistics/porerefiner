# -*- coding: utf-8 -*-

"""Main module."""

import click
import daemon
import datetime
import json
import logging
import sys, os
import yaml

from asyncio import run, gather, wait
from porerefiner import models
from porerefiner.models import Job
import porerefiner.jobs.submitters as submitters
from pathlib import Path

from porerefiner.rpc import start_server
from porerefiner.fsevents import start_fs_watchdog, start_run_end_polling, start_job_polling, in_progress_run_update

log = logging.getLogger('porerefiner.service')





async def serve(config_file, db_path=None, db_pragmas=None, wdog_settings=None, server_settings=None, system_settings=None):
    "Initialize and gather coroutines"
    if not all([db_path, db_pragmas, wdog_settings, server_settings, system_settings]): #need to defer loading config for testing purposes
        from porerefiner.config import Config
        config = Config(config_file).config
        db_path=config['database']['path']
        db_pragmas=config['database']['pragmas']
        wdog_settings=config['nanopore']
        server_settings=config['server']
        system_settings=config['porerefiner']
    models._db.init(db_path, db_pragmas)
    [cls.create_table(safe=True) for cls in models.REGISTRY]
    try:
        results = await gather(start_server(**server_settings),
                    start_fs_watchdog(**wdog_settings),
                    start_run_end_polling(**system_settings),
                    start_job_polling(**system_settings),
                    in_progress_run_update())
    finally:
        log.critical("Shutting down...")

default_config = lambda: os.environ.get('POREREFINER_CONFIG', Path.home() / '.porerefiner' / 'config.yaml')


@click.group()
@click.option('-v', '--verbose', is_flag=True)
def cli(verbose):
    logging.basicConfig(stream=sys.stdout, level=(logging.CRITICAL, logging.DEBUG)[verbose])

@cli.command()
@click.option('--config', prompt='path to config file', default = default_config)
@click.option('--nanopore_dir')
def init(config, nanopore_dir=None):
    "Find the Nanopore output directory and create the config file."
    if click.prompt(f"create PoreRefiner config at {config}?"):
        pass

@cli.command()
@click.option('--config', prompt='path to config file', default = default_config)
@click.option('-d', '--daemonize', 'demonize', is_flag=True, default=False)
def start(config, demonize=False):
    "Start the PoreRefiner service."
    log = logging.getLogger('porerefiner')
    if demonize:
        log.info("Starting daemon...")
        with daemon.DaemonContext():
            run(serve(config))
    else:
        log.info("Starting server...")
        run(serve(config))
    return 0

@cli.group()
def reset():
    "Utility function to reset various state."
    pass

@reset.command()
@click.argument('status', default="QUEUED", type=click.Choice([v for v, _ in Job.statuses], case_sensitive=True))
def jobs(status): #TODO
    "Reset all jobs to a particular status."
    if click.confirm(f"This will set all jobs to {status} status. Are you sure?"):
        click.echo("reset jobs")

@reset.command()
def runs(): #TODO
    "Reset all runs to in-progress status."
    if click.confirm(f"This will set all runs to in-progress status, triggering notifiers and jobs in the next hour. Are you sure?"):
        click.echo("reset runs")

# @reset.command()
# def config():
#     "Reset config to defaults."
#     if click.confirm("This will reset your config to defaults. Are you sure?"):
#         try:
#             import importlib
#             import porerefiner.config
#             porerefiner.config.config_file.unlink()
#             importlib.reload(porerefiner.config)
#         except Exception:
#             from os import environ
#             config_file = Path(environ.get('POREREFINER_CONFIG', '/Users/justin.payne/.porerefiner/config.yml'))
#             config_file.unlink()
#             import porerefiner.config

@reset.command()
def database():
    "Reset database to empty state."
    if click.confirm("This will delete the porerefiner database. Are you sure?"):
        import porerefiner.config
        Path(porerefiner.config.config['database']['path']).unlink()

@reset.command()
def samplesheets(): #TODO
    "Clear samplesheets that aren't attached to any run."
    click.echo("clear sheets")

@cli.group(name="list")
def _list():
    "List job system stuff."
    pass

@_list.command(name='jobs')
def _jobs():
    "List the configurable and configured jobs."
    import porerefiner.jobs
    click.echo("Installed job modules:")
    click.echo(yaml.dump(list(porerefiner.jobs.REGISTRY.keys())))
    import porerefiner.config
    click.echo("Configured jobs:")
    click.echo(yaml.dump(porerefiner.jobs.JOBS))

@_list.command(name='submitters')
def _submitters():
    "List the configureable and configured submitters."
    import porerefiner.jobs
    click.echo("Installed submitters:")
    click.echo(yaml.dump(list(porerefiner.jobs.submitters.REGISTRY.keys())))
    import porerefiner.config
    click.echo("Configured submitters:")
    click.echo(yaml.dump(porerefiner.jobs.submitters.SUBMITTERS))

@_list.command()
def notifiers():
    "List the configurable and configured notifiers."
    import porerefiner.notifiers
    click.echo("Installed notifiers:")
    click.echo(yaml.dump(list(porerefiner.notifiers.REGISTRY.keys())))
    import porerefiner.config
    click.echo("Configured notifiers:")
    click.echo(yaml.dump(porerefiner.notifiers.NOTIFIERS))

@cli.group()
def verify():
    "Run various checks."
    pass

@verify.command(name='submitters')
def _submitters():
    "Verify configuration of job submitters by running their tests."
    async def test_all():
        for submitter in submitters.SUBMITTERS:
            click.echo(f'Running {type(submitter).__name__} integration no-op test')
            await submitter.test_noop()
    run(test_all())

@verify.command()
def notifiers():
    "Verify notifiers by sending notifications."
    from porerefiner.notifiers import NOTIFIERS
    async def test_all():
        for notifier in NOTIFIERS:
            click.echo(f"Running {type(notifier).__name__}")
            await notifier.notify(None)
    run(test_all())




if __name__ == '__main__':
    sys.exit(cli())                   # pragma: no cover
