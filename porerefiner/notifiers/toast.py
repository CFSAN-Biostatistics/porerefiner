import asyncio
import logging
from dataclasses import dataclass

from porerefiner.notifiers import Notifier

log = logging.getLogger('porerefiner.toast_notifier')

@dataclass
class ToastNotifier(Notifier): #TODO
    "Notifier that throws up an OS 'toast' on Windows, Ubuntu, and CentOS"

    async def notify(self, run, state, message):
        try:
            from pynotifier import Notification
            Notification(title=message,
                         description=f"run {run.alt_name} ({run.path}) completed.",
                         duration=10).send()
        except ImportError:
            log.error(f"Toast notifier configured but py-notifier not installed. Please install py-notifier (pip install py-notifier) for OS toast notifications.")
        except SystemError:
            log.error(f"Toast notifier configured but py-notifier doesn't work under Mac OS X.")
