
from dataclasses import dataclass
from porerefiner.jobs.submitters import Submitter
from asyncio import subprocess


@dataclass
class LocalSubmitter(Submitter):

    async def test_noop(self):
        pass

    def reroot_path(self, path):
        return path #no op, no need to reroot paths

    async def begin_job(self, command, datadir, remotedir, environment_hints={}):
        self.process = await subprocess.create_subprocess_shell(command)

    async def poll_job(self, job):
        await self.process.wait()
        if self.process.returncode:
            return 'FAILED'
        return 'DONE'

    def closeout_job(self, job, datadir, remotedir):
        pass


