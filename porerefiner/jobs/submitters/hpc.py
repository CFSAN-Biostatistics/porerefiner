from dataclasses import dataclass
from asyncssh import connect
from pathlib import Path
from typing import Union


from porerefiner.jobs.submitters import Submitter, Url, Email, Path

import asyncio
import subprocess

@dataclass
class HpcSubmitter(Submitter):
    "Job submitter for interfacing with HPC resources."

    login_host: str
    username: str
    private_key_path: str
    known_hosts_path: str
    scheduler: str = "uge"
    queue: str = "long.q"
    remote_root: str = "~"

    async def send(self, cmd):
        "Run a command over SSH and return its stdout as a stripped string."
        async with connect(self.login_host,
                        username=self.username,
                        client_keys=[self.private_key_path],
                        known_hosts=self.known_hosts_path) as conn:
            result = await conn.run(cmd, check=True)
            return str(result.stdout).strip()

    async def test_noop(self):
        subprocess.run(['rsync', '--version']).check_returncode()
        self.remote_root = Path(await self.send('python -c "import tempfile; print(tempfile.gettempdir())"'))


    def reroot_path(self, path):
        return Path(self.remote_root, path)

    async def begin_job(self, command, datadir, remotedir, environment_hints={}):
        hints = " ".join([f"{name}={value}" for name, value in environment_hints.items()])
        return await self.send(f'''echo "{hints} {command}" | qsub -q {self.queue}''')

    async def poll_job(self, job):
        "Return the job's scheduler status. qstat lists active jobs; absence => completed."
        active = await self.send("qstat")
        if job.job_id and job.job_id in active:
            return 'RUNNING'
        return 'DONE'

    async def closeout_job(self, job, datadir, remotedir):
        pass
