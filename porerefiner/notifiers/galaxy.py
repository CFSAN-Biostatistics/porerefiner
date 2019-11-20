import asyncio
import logging

from porerefiner.notifiers import Notifier

log = logging.getLogger('porerefiner.galaxy_notifier')

class GalaxyTrakrNotifier(Notifier):

    def __init__(self, name, api_key, *a, **k):
        super().__init__(name)
        self.api_key = api_key

    async def notify(self, run, state, message): #TODO
        "Send this run into the GalaxyTrakr environment, under a configured username"
        try:
            import bioblend
            gt = bioblend.galaxy.GalaxyInstance(url=self.name, api=self.api_key)

        except ImportError:
            log.error("GalaxyTrakr notifier enabled, but BioBlend not installed.")

        except Exception as e:
            log.error(f"Galaxy connection to {self.name}, error is {e}")
