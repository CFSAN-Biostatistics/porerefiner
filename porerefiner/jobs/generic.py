
from dataclasses import dataclass, field
from os import environ

from porerefiner.jobs import FileJob, RunJob

@dataclass
class GenericFileJob(FileJob):

    command: str
    hints: dict = field(default_factory=dict)

    def setup(self, run, file, datadir, remotedir):
        locals().update(environ)
        return self.command.format(**locals())

    def collect(*args, **kwargs):
        pass

@dataclass
class GenericRunJob(RunJob):

    command: str
    hints: dict = field(default_factory=dict)

    def setup(self, run, datadir, remotedir):
        locals().update(environ)
        return self.command.format(**locals())

    def collect(*args, **kwargs):
        pass
