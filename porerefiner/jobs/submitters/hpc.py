from porerefiner.jobs.submitters import Submitter


class HpcSubmitter(Submitter):

    def test_noop(self):
        return False

    def reflect_path(self, path):
        return path

    async def begin_job(self, command, datadir, remotedir, environment_hints={}):
        return "0000"

    async def poll_job(self, job):
        return "RUNNING"

    def closeout_job(self, job, datadir, remotedir):
        pass
