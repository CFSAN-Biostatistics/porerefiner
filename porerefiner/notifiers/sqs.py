import asyncio
import logging
import json

from dataclasses import dataclass

from porerefiner.notifiers import Notifier

log = logging.getLogger('porerefiner.sqs_notifier')

@dataclass
class SqsNotifier(Notifier): #TODO
    "Send a message to an SQS queue, requires Boto3"

    queue: str = "porerefiner-messages"


    async def notify(self, run, state, message):
        try:
            import boto3
            sqs = boto3.resource('sqs')
            q = sqs.get_queue_by_name(QueueName=self.queue)
            attrs = dict(State=dict(StringVal=str(state), DataType='String'),
                         Message=dict(StringVal=str(message), DataType='String'))
            response = q.send_message(MessageBody=json.dumps(run), MessageAttributes=attrs)
            log.info("SQS mesage sent.")

        except ImportError:
            log.error("SQS notifier enabled, but Boto3 not installed.")
        except Exception as e:
            log.error(f"Error sending SQS message: {e}")
