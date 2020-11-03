
from dataclasses import dataclass, field
from os import environ
from typing import List

from porerefiner.jobs import FileJob, RunJob

@dataclass
class GenericFileJob(FileJob):

    commands: List[str] = field(default_factory=list)
    hints: dict = field(default_factory=dict)

    def run(self, run, file, datadir, remotedir):
        locals().update(environ)
        for command in self.commands:
            yield command.format(**locals())

@dataclass
class GenericRunJob(RunJob):

    commands: List[str] = field(default_factory=list)
    hints: dict = field(default_factory=dict)

    def run(self, run, datadir, remotedir):
        locals().update(environ)
        for command in self.commands:
            yield command.format(**locals())
