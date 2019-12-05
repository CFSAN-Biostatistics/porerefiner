from dataclasses import dataclass

from porerefiner.jobs.submitters import Submitter

@dataclass
class Epi2meSubmitter(Submitter): #TODO

    api_key: str

    async def test_noop(self):
        return False

    def reroot_path(self, path):
        return path

    async def begin_job(self, command, datadir, remotedir, environment_hints={}):
        return "0000"

    async def poll_job(self, job):
        return "RUNNING"

    def closeout_job(self, job, datadir, remotedir):
        pass
