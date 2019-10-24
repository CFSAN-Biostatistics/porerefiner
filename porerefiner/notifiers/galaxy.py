import asyncio

from porerefiner.notifiers import Notifier
from logging import log

class GalaxyTrakrNotifier(Notifier):

    async def notify(self, run, state, message): #TODO
        "Send this run into the GalaxyTrakr environment, under a configured username"
        try:
            import bioblend

        except ImportError:
            log.error("GalaxyTrakr notifier enabled, but BioBlend not installed.")
