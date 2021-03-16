
from dataclasses import dataclass, field
from os import environ
from typing import List

from porerefiner.jobs import FileJob, RunJob

@dataclass
class GenericFileJob(FileJob):

    on_complete_commands: List[str] = field(default_factory=list)
    on_complete_hints: dict = field(default_factory=dict)
    on_new_commands: List[str] = field(default_factory=list)
    on_new_hints: dict = field(default_factory=dict)

    def on_complete(self, run, file, datadir, remotedir):
        namespace = {}
        namespace.update(globals())
        namespace.update(locals())
        namespace.update(environ)
        for command in self.on_complete_commands:
            yield command.format(**namespace)

@dataclass
class GenericRunJob(RunJob):

    on_complete_commands: List[str] = field(default_factory=list)
    on_complete_hints: dict = field(default_factory=dict)
    on_new_commands: List[str] = field(default_factory=list)
    on_new_hints: dict = field(default_factory=dict)

    def on_complete(self, run, datadir, remotedir):
        namespace = {}
        namespace.update(globals())
        namespace.update(locals())
        namespace.update(environ)
        for command in self.on_complete_commands:
            yield command.format(**namespace)
