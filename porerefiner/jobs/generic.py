
from dataclasses import dataclass, field
from os import environ
from typing import List

from porerefiner.jobs import FileJob, RunJob

@dataclass
class GenericFileJob(FileJob):

    commands: List[str] = field(default_factory=list)
    hints: dict = field(default_factory=dict)

    def run(self, run, file, datadir, remotedir):
        namespace = {}
        namespace.update(globals())
        namespace.update(locals())
        namespace.update(environ)
        for command in self.commands:
            yield command.format(**namespace)

@dataclass
class GenericRunJob(RunJob):

    commands: List[str] = field(default_factory=list)
    hints: dict = field(default_factory=dict)

    def run(self, run, datadir, remotedir):
        namespace = {}
        namespace.update(globals())
        namespace.update(locals())
        namespace.update(environ)
        for command in self.commands:
            yield command.format(**namespace)
