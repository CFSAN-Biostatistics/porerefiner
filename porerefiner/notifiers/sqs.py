import asyncio

from porerefiner.notifiers import Notifier
from logging import log

class SqsNotifier(Notifier): #TODO
    "Send a message to an SQS queue, requires Boto3"

    async def notify(self, run, state, message):
        try:
            import boto3

        except ImportError:
            log.error("SQS notifier enabled, but Boto3 not installed.")
