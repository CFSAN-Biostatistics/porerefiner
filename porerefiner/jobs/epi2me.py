from porerefiner.jobs import RunJob

class EpiJob(RunJob):

    def setup(self, run, datadir, remotedir):
        pass

    def collect(self, run, datadir, pid):
        pass
