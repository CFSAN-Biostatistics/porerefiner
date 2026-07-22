"Tests for the SQS notifier."

import sys
from types import ModuleType
from unittest.mock import MagicMock

from pytest import mark

from porerefiner.notifiers import REGISTRY
from porerefiner.notifiers.sqs import SqsNotifier


def test_sqs_notifier_registered():
    assert 'SqsNotifier' in REGISTRY


def test_sqs_notifier_configurable():
    assert 'queue' in SqsNotifier.__dataclass_fields__


@mark.asyncio
async def test_sqs_notify_serializes_run(monkeypatch):
    notifier = SqsNotifier(name="test", queue="a-queue")

    queue = MagicMock()
    resource = MagicMock()
    resource.get_queue_by_name.return_value = queue
    fake_boto3 = ModuleType("boto3")
    fake_boto3.resource = MagicMock(return_value=resource)

    monkeypatch.setitem(sys.modules, "boto3", fake_boto3)

    # run is a non-JSON-serializable object; notifier must stringify it
    class Run:
        def __str__(self):
            return "run-repr"

    await notifier.notify(run=Run(), state="DONE", message="finished")

    resource.get_queue_by_name.assert_called_once_with(QueueName="a-queue")
    queue.send_message.assert_called_once()
    _, kwargs = queue.send_message.call_args
    assert "run-repr" in kwargs['MessageBody']
    assert kwargs['MessageAttributes']['State']['StringValue'] == "DONE"


@mark.asyncio
async def test_sqs_notify_handles_missing_boto3(monkeypatch):
    "No boto3 installed -> logs error, does not raise."
    notifier = SqsNotifier(name="test", queue="a-queue")
    monkeypatch.setitem(sys.modules, "boto3", None)  # forces ImportError on import
    await notifier.notify(run="r", state="s", message="m")
