import logging
from contextlib import contextmanager

log = logging.getLogger('porerefiner.daemon')

try:
    import daemon
except ModuleNotFoundError:
    log.critical("Couldn't import python-daemon.")
    log.critical("Might be running under Windows where daemonization isn't supported.")

    class HalfDaemon:

        @contextmanager
        def DaemonContext(self):
            raise NotImplementedError("Daemonization not supported under Windows.")
            yield

    daemon = HalfDaemon()