
import asyncio
import logging
import timeit

from pathlib import Path
from uuid import uuid4
from random import choice, randint
from tempfile import TemporaryDirectory
from threading import Thread
from os import makedirs

import click

from peewee import SqliteDatabase
from porerefiner import models
from porerefiner.fsevents import start_fs_watchdog

def start_pr(path):
    

    loop = asyncio.new_event_loop()



    def l(loop):
        logging.basicConfig(stream=open('/dev/null', 'w'))
        db = SqliteDatabase(":memory:", pragmas={'foreign_keys':1}, autoconnect=False)
        db.bind(models.REGISTRY, bind_refs=False, bind_backrefs=False)
        db.connect()
        db.create_tables(models.REGISTRY)
        asyncio.set_event_loop(loop)
        loop.run_forever()
        click.echo(f"{models.Run.select().count()} runs, {models.File.select().count()} files")
        db.drop_tables(models.REGISTRY)
        db.close()


    # future = asyncio.ensure_future(start_fs_watchdog(path))
    # loop.call_soon_threadsafe(future)

    future = asyncio.run_coroutine_threadsafe(start_fs_watchdog(path, loop=loop), loop)

    t = Thread(target=l, args=[loop])
    t.start()

    return loop, future


def stop_pr(loop, future):

    loop.stop()
    future.cancel()
    # while loop.is_running():
    #     pass
    # loop.close()

    

@click.command()
@click.argument('n', default=3000)
def main(n, trials=5):

    with TemporaryDirectory() as t:

        path = Path(t) / "EXPERIMENTEXPERIMENT" / "SAMPLESAMPLE"

        for run in ['RUN_1_RUN', 'RUN_2_RUN']:
            for sub in ['fastq_pass', 'fastq_fail']:
                makedirs(path / run / sub)
    
        def fs_spray(n):
            print(f"opening {n} files")
            fps = [open(path / choice(['RUN_1_RUN', 'RUN_2_RUN']) / choice(['fastq_pass', 'fastq_fail', '']) / (str(uuid4()) + '.bin'), 'wb', buffering=0) for _ in range(n)]
            print(f"100,000 {len(bytes(str(uuid4()), 'utf-8'))}-byte writes to {n} files")
            for _ in range(100000):
                choice(fps).write(bytes(str(uuid4()), 'utf-8'))
            [fp.close() for fp in fps]
            # print(f"100,000 {len(bytes(str(uuid4()), 'utf-8'))}-byte writes to {n} files")

        click.echo("Spraying filesystem for baseline...")
        basetime = timeit.timeit("fs_spray(n)", number=trials, globals=locals())
        click.echo(f"{basetime:03} seconds.")
        click.echo("Setting up filesystem event watcher...")
        loop, future= start_pr(t)
        click.echo("Spraying filesystem under watchdog...")
        realtime = timeit.timeit("fs_spray(n)", number=trials, globals=locals())
        click.echo(f"{realtime:03} seconds.")
        click.echo("Bringing down watchdog thread...")
        stop_pr(loop, future)
        #click.echo(basetime)
        #click.echo(realtime)
        click.echo(f"{realtime - basetime:02} seconds difference.")

if __name__ == '__main__':
    quit(main())
