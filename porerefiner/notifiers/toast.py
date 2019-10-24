import asyncio

from porerefiner.notifiers import Notifier

class ToastNotifier(Notifier): #TODO
    "Notifier that throws up an OS 'toast' on Windows, Ubuntu, and CentOS"

    async def notify(self, run, state, message):
        pass
