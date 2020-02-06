import asyncio
import pkgutil
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

    def __call__(cls, *args, **kwargs):
        the_instance = super().__call__(*args, **kwargs)
        NOTIFIERS.append(the_instance)
        return the_instance


class Notifier(metaclass=_MetaRegistry):
    "Abstract base class for notifiers"

    def __init__(self, name, *args, **kwargs):
        super().__init__()
        self.name = name

    async def notify(self, run, state, message):
        raise NotImplementedError('Notifier not implemented.')



NOTIFIERS = []

# from . import galaxy
# from . import http
# from . import sqs
# from . import toast

for loader, module_name, is_pkg in  pkgutil.walk_packages(__path__):
    _module = loader.find_module(module_name).load_module(module_name)
    globals()[module_name] = _module

