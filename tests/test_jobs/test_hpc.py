from types import SimpleNamespace
from pathlib import Path
from unittest.mock import AsyncMock, patch

from pytest import mark

from porerefiner.jobs.submitters import REGISTRY
from porerefiner.jobs.submitters.hpc import HpcSubmitter


def make_submitter():
    return HpcSubmitter(
        login_host="login.test",
        username="tester",
        private_key_path="/dev/null",
        known_hosts_path="/dev/null",
    )


def test_hpc_registered():
    assert 'HpcSubmitter' in REGISTRY


def test_reroot_path():
    sub = make_submitter()
    sub.remote_root = "/scratch"
    assert sub.reroot_path("data/x") == Path("/scratch/data/x")


@mark.asyncio
async def test_begin_job_builds_qsub():
    sub = make_submitter()
    with patch.object(sub, 'send', new_callable=AsyncMock) as send:
        send.return_value = "Your job 12345 has been submitted"
        result = await sub.begin_job("echo hi", "/tmp/d", "/scratch/d",
                                     environment_hints={"NCORES": "4"})
        assert result == "Your job 12345 has been submitted"
        cmd = send.call_args[0][0]
        assert "qsub" in cmd
        assert "NCORES=4" in cmd
        assert sub.queue in cmd


@mark.asyncio
async def test_poll_job_running_then_done():
    sub = make_submitter()
    job = SimpleNamespace(job_id="12345")
    with patch.object(sub, 'send', new_callable=AsyncMock) as send:
        send.return_value = "job-ID  prior   name   ...\n12345  0.5  myjob  r"
        assert await sub.poll_job(job) == 'RUNNING'
        send.return_value = "no active jobs"
        assert await sub.poll_job(job) == 'DONE'
