# -*- coding: utf-8 -*-

"""Main module."""

import click
import daemon
import datetime
import json
import logging
import setproctitle
import sys, os
import yaml

from asyncio import run, gather, wait
from porerefiner import models
from porerefiner.models import Job, Run
import porerefiner.cli_utils as cli_utils
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

# bit of complexity here to handle different defaults for privileged vs normal users

default_config = lambda: os.environ.get('POREREFINER_CONFIG',
                                        lambda: (Path.home() / '.porerefiner' / 'config.yaml',
                                                Path('/etc/porerefiner/config.yaml'))[os.geteuid == 0])

config = click.option('--config',
                      prompt=('path to config file', False)['POREREFINER_CONFIG' in os.environ],
                      default=default_config(),
                      show_envvar=True,
                      type=cli_utils.PathPath())


@click.group()
@click.option('-v', '--verbose', is_flag=True)
def cli(verbose):
    logging.basicConfig(stream=sys.stdout,
                        style='{',
                        format="{levelname} {module}:{message}",
                        level=(logging.ERROR, logging.INFO)[verbose])

@cli.command()
@config
@click.option('--nanopore_dir')
@click.option('--client', '-c', 'client_only', is_flag=True)
def init(config, nanopore_dir='/var/lib/minknow/data', client_only=False):
    "Find the Nanopore output directory and create the config file."
    if config.exists():
        if click.confirm(f"delete existing config file at {config}?"):
            config.unlink()
    if click.confirm(f"create PoreRefiner config at {config}?"):
        sock_path = click.prompt(f"location of porerefiner RPC socket?", default=config.parent / 'porerefiner.sock', show_default=True)
        if not client_only:
            db_path = click.prompt(f"location of database?", default=config.parent / 'database.db', show_default=True)
            nan_path = click.prompt("nanopore data output location?", default=nanopore_dir, show_default=True)
        from porerefiner.config import Config
        Config.new_config_file(config, client_only=client_only, database_path=db_path, socket_path=sock_path)
        click.echo(f'''export POREREFINER_CONFIG="{config}"''')

@cli.command()
@config
@click.option('-d', '--daemonize', 'demonize', is_flag=True, default=False)
def start(config, demonize=False):
    "Start the PoreRefiner service."
    setproctitle.setproctitle("porerefiner")
    log = logging.getLogger('porerefiner')
    if demonize:
        log.info("Starting daemon...")
        with daemon.DaemonContext():
            run(serve(config))
    else:
        log.info("Starting server, ctl-C to stop.")
        run(serve(config))
    return 0

@cli.group()
def reset():
    "Utility function to reset various state."
    pass

@reset.command()
@click.argument('status', default="QUEUED", type=click.Choice([v for v, _ in Job.statuses], case_sensitive=True))
def jobs(status):
    "Reset all jobs to a particular status."
    if click.confirm(f"This will set all jobs to {status} status. Are you sure?"):
        Job.update(status=status).execute()
        click.echo(f"Jobs set to {status}.")

@reset.command()
@click.argument('status', default="RUNNING", type=click.Choice([v for v, _ in Run.statuses], case_sensitive=True))
@click.option('--run', 'run_name', default=None)
@config
def runs(status, config, run_name=None):
    "Reset all runs to in-progress status."
    from porerefiner.config import Config
    config = Config(config).config
    db_path=config['database']['path']
    db_pragmas=config['database']['pragmas']
    models._db.init(db_path, db_pragmas)
    if run_name:
        if click.confirm("This will set run {run_name} to {status} status. Are you sure?"):
            Run.update(status=status).where(alt_name=run_name).execute()
            click.echo(f"Run {run_name} set to {status}.")
    else:
        if click.confirm(f"This will set all runs to {status} status, triggering notifiers and jobs in the next hour. Are you sure?"):
            Run.update(status=status).execute()
            click.echo(f'Runs set to {status}.')

@reset.command()
@config
def database(config):
    "Reset database to empty state."
    if click.confirm("This will delete the porerefiner database. Are you sure?"):
        import porerefiner.config
        Path(porerefiner.config.Config(config).config['database']['path']).unlink()

@reset.command()
def samplesheets(): #TODO
    "Clear samplesheets that aren't attached to any run."
    click.echo("clear sheets")

@cli.group(name="list")
@config
def _list(config):
    "List job system stuff."
    from porerefiner.config import Config
    config = Config(config).config
    db_path=config['database']['path']
    db_pragmas=config['database']['pragmas']
    models._db.init(db_path, db_pragmas)

@_list.command(name='jobs')
def _jobs():
    "List the configurable, configured, and spawned jobs."
    import porerefiner.jobs
    click.echo("Installed job modules:")
    click.echo(yaml.dump(list(porerefiner.jobs.REGISTRY.keys())))
    click.echo("Configured jobs:")
    click.echo(yaml.dump(porerefiner.jobs.JOBS))
    click.echo("Spawned jobs:")
    [click.echo(yaml.dump(job)) for job in Job.select().dicts()]

@_list.command(name='submitters')
def _submitters():
    "List the configureable and configured submitters."
    import porerefiner.jobs
    click.echo("Installed submitters:")
    click.echo(yaml.dump(list(porerefiner.jobs.submitters.REGISTRY.keys())))
    click.echo("Configured submitters:")
    click.echo(yaml.dump(porerefiner.jobs.submitters.SUBMITTERS))

@_list.command()
def notifiers():
    "List the configurable and configured notifiers."
    import porerefiner.notifiers
    click.echo("Installed notifiers:")
    click.echo(yaml.dump(list(porerefiner.notifiers.REGISTRY.keys())))
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
