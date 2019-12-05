
from dataclasses import dataclass, field

from porerefiner.jobs import FileJob, RunJob

@dataclass
class GenericFileJob(FileJob):

    command: str
    hints: dict = field(default_factory=dict)

    def setup(self, run, file, datadir, remotedir):
        return self.command.format(**locals())

    def collect(*args, **kwargs):
        pass

@dataclass
class GenericRunJob(RunJob):

    command: str
    hints: dict = field(default_factory=dict)

    def setup(self, run, datadir, remotedir):
        return self.command.format(**locals())

    def collect(*args, **kwargs):
        pass
