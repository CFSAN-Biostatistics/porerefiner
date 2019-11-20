import asyncio
import aiohttp
import logging

log = logging.getLogger('porerefiner.http_notifier')

from porerefiner.notifiers import Notifier

class HttpCallbackNotifier(Notifier):

    sample_name = "http://sample.url/api/"


    async def notify(self, run, state, message): #TODO
        "Send a message to the configured URL via http-form POST"
        log.info(f"Notifying {self.name}...")
        async with aiohttp.ClientSession() as session:
            async with self.session.post(self.name, data=dict(run=run, state=state, message=message)) as response:
                log.info(response.status)
                log.info(response.text)
