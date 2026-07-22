"Bounded scale tests: ensure bulk model + event handling stays correct and finishes."

import time
from pathlib import Path
from tempfile import TemporaryDirectory

from pytest import mark

from tests import db, Event  # noqa: F401  (db fixture, Event namedtuple)

from porerefiner import models
from porerefiner.fsevents import PoreRefinerFSEventHandler as Handler


def test_bulk_run_creation(db):
    "Creating many runs should be correct and reasonably fast."
    start = time.perf_counter()
    with db.atomic():
        for i in range(500):
            models.Run.create(name=f"run_{i}", path=f"/data/run_{i}")
    elapsed = time.perf_counter() - start
    assert models.Run.select().count() == 500
    assert elapsed < 30, f"bulk insert too slow: {elapsed:.1f}s"


@mark.asyncio
async def test_many_file_events(db):
    "The event handler should register many files under one run without error."
    with TemporaryDirectory() as t:
        base = Path(t)
        run_dir = base / "EXP" / "SAMPLE" / "20240101_dev_fc_run"
        (run_dir / "fastq_pass").mkdir(parents=True)
        handler = Handler(base)
        for i in range(50):
            fp = run_dir / "fastq_pass" / f"read_{i}.fastq"
            fp.write_text("data")
            await handler.on_created(Event(fp, False))
        assert models.Run.select().count() == 1
        assert models.File.select().count() == 50
