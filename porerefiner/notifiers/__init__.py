import asyncio
# from ..models import PorerefinerModel

# states = PorerefinerModel.statuses

REGISTRY = {}


def _register_class(target_class):
    REGISTRY[target_class.__name__] = target_class

class _MetaRegistry(type):

    def __new__(meta, name, bases, class_dict):
        cls = type.__new__(meta, name, bases, class_dict)
        if name not in REGISTRY:
            _register_class(cls)
        return cls

class Notifier(metaclass=_MetaRegistry):
    "Abstract base class for notifiers"

    async def notify(self, run, state, message):
        raise NotImplementedError('Notifier not implemented.')

    @classmethod
    def to_yaml(cls): #TODO
        pass



NOTIFIERS = []


