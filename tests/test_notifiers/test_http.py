"Tests for the HTTP callback notifier."

from unittest.mock import AsyncMock, MagicMock, patch

from pytest import mark

from porerefiner.notifiers import REGISTRY
from porerefiner.notifiers.http import HttpCallbackNotifier


def test_http_notifier_registered():
    assert 'HttpCallbackNotifier' in REGISTRY


def test_http_notifier_configurable():
    # url is a configurable dataclass field, not the abstract 'name'-only base
    assert 'url' in HttpCallbackNotifier.__dataclass_fields__


@mark.asyncio
async def test_http_notify_posts_to_url():
    notifier = HttpCallbackNotifier(name="test", url="http://example.test/hook")

    # Build an async-context-manager mock chain for aiohttp
    response = MagicMock()
    response.status = 200
    response.text = AsyncMock(return_value="ok")

    post_ctx = MagicMock()
    post_ctx.__aenter__ = AsyncMock(return_value=response)
    post_ctx.__aexit__ = AsyncMock(return_value=False)

    session = MagicMock()
    session.post = MagicMock(return_value=post_ctx)

    session_ctx = MagicMock()
    session_ctx.__aenter__ = AsyncMock(return_value=session)
    session_ctx.__aexit__ = AsyncMock(return_value=False)

    with patch('porerefiner.notifiers.http.aiohttp.ClientSession', return_value=session_ctx):
        await notifier.notify(run="run-1", state="DONE", message="finished")

    session.post.assert_called_once()
    args, kwargs = session.post.call_args
    assert args[0] == "http://example.test/hook"
    assert kwargs['data']['message'] == "finished"
