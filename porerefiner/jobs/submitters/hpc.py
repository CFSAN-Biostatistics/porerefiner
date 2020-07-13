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
        async with connect(self.login_host,
                        username=self.username,
                        client_keys=[self.private_key_path],
                        known_hosts=self.known_hosts_path) as conn:
            return await conn.run(cmd)

    async def test_noop(self):
        subprocess.run(['rsync', '--version']).check_returncode()
        self.remote_root = Path((await self.send('python -c "import tempfile; print(tempfile.gettempdir())"')).strip())


    def reroot_path(self, path):
        return Path(self.remote_root, path)

    async def begin_job(self, command, datadir, remotedir, environment_hints={}):
        hints = " ".join([f"{name}={value}" for name, value in environment_hints.items()])
        return await self.send(f'''echo "{hints} {command}" | qsub -q {self.queue}''')

    async def poll_job(self, job):
        result = await self.send(f"qacct")

    def closeout_job(self, job, datadir, remotedir):
        pass
