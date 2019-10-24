import asyncio

from porerefiner.notifiers import Notifier

class HttpCallbackNotifier(Notifier):

    async def notify(self, run, state, message): #TODO
        "Send a message to the configured URL via http-form POST"
        pass
