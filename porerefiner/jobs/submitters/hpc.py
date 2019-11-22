from dataclasses import dataclass
from asyncssh import connect
from typing import Union


from porerefiner.jobs.submitters import Submitter

import asyncio
import subprocess

@dataclass
class HpcSubmitter(Submitter):

    login_host: str
    username: str
    private_key_path: str
    known_hosts_path: str
    scheduler: str = "uge"
    queue: str = "long.q"

    async def send(self, cmd):
        async with connect(self.login_host,
                        username=self.username,
                        client_keys=[self.private_key_path],
                        known_hosts=known_hosts_path) as conn:
            return await conn.run(cmd)

    def test_noop(self):
        subprocess.run(['rsync', '--version']).check_returncode()
        return asyncio.get_event_loop().run_until_complete(self.send('ls ~'))


    def reroot_path(self, path):
        return path

    async def begin_job(self, command, datadir, remotedir, environment_hints={}):
        return "0000"

    async def poll_job(self, job):
        result = await self.send(f"qacct")

    def closeout_job(self, job, datadir, remotedir):
        pass
