import asyncio
import aiohttp
import logging
from dataclasses import dataclass

log = logging.getLogger('porerefiner.http_notifier')

from porerefiner.notifiers import Notifier

@dataclass
class HttpCallbackNotifier(Notifier):

    name: str = "HttpCallbackNotifier"
    url: str = "http://sample.url/api/"


    async def notify(self, run, state, message):
        "Send a message to the configured URL via http-form POST"
        log.info(f"Notifying {self.name} at {self.url}...")
        async with aiohttp.ClientSession() as session:
            async with session.post(self.url, data=dict(run=str(run), state=str(state), message=message)) as response:
                log.info(response.status)
                log.info(await response.text())
