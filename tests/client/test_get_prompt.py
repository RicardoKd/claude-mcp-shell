import os
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from mcp_client import MCPClient


@pytest.fixture
def anyio_backend():
    return "asyncio"


def make_client_with_session(session):
    client = MCPClient(command="uv", args=["run", "mcp_server.py"])
    client._session = session
    return client


@pytest.mark.anyio
async def test_happy_path_returns_messages_list():
    fake_message_a = SimpleNamespace(role="user", content="hello")
    fake_message_b = SimpleNamespace(role="user", content="world")
    fake_result = SimpleNamespace(messages=[fake_message_a, fake_message_b])

    session = SimpleNamespace(get_prompt=AsyncMock(return_value=fake_result))
    client = make_client_with_session(session)

    messages = await client.get_prompt("summarize-doc", {"filename": "notes.md"})

    assert messages == [fake_message_a, fake_message_b]
    session.get_prompt.assert_awaited_once_with(
        "summarize-doc", {"filename": "notes.md"}
    )


@pytest.mark.anyio
async def test_returns_messages_attribute_not_full_result():
    fake_message = SimpleNamespace(role="user", content="hi")
    fake_result = SimpleNamespace(messages=[fake_message])

    session = SimpleNamespace(get_prompt=AsyncMock(return_value=fake_result))
    client = make_client_with_session(session)

    result = await client.get_prompt("rewrite-as-markdown", {"filename": "notes.md"})

    # Must return result.messages, not the whole GetPromptResult.
    assert result is not fake_result
    assert result == [fake_message]


@pytest.mark.anyio
async def test_returns_empty_list_when_no_messages():
    fake_result = SimpleNamespace(messages=[])

    session = SimpleNamespace(get_prompt=AsyncMock(return_value=fake_result))
    client = make_client_with_session(session)

    messages = await client.get_prompt("summarize-doc", {"filename": "notes.md"})

    assert messages == []


@pytest.mark.anyio
async def test_args_are_passed_through_unchanged():
    fake_result = SimpleNamespace(messages=[])
    session = SimpleNamespace(get_prompt=AsyncMock(return_value=fake_result))
    client = make_client_with_session(session)

    args = {"filename": "report.md", "extra": "value"}
    await client.get_prompt("rewrite-as-markdown", args)

    session.get_prompt.assert_awaited_once_with("rewrite-as-markdown", args)


@pytest.mark.anyio
async def test_empty_args_dict_passed_through():
    fake_result = SimpleNamespace(messages=[])
    session = SimpleNamespace(get_prompt=AsyncMock(return_value=fake_result))
    client = make_client_with_session(session)

    await client.get_prompt("some-prompt", {})

    session.get_prompt.assert_awaited_once_with("some-prompt", {})


@pytest.mark.anyio
async def test_raises_connection_error_when_not_connected():
    client = MCPClient(command="uv", args=["run", "mcp_server.py"])

    with pytest.raises(ConnectionError):
        await client.get_prompt("summarize-doc", {"filename": "notes.md"})


@pytest.mark.anyio
async def test_propagates_sdk_exception_unchanged():
    class CustomSDKError(Exception):
        pass

    session = SimpleNamespace(
        get_prompt=AsyncMock(side_effect=CustomSDKError("boom"))
    )
    client = make_client_with_session(session)

    with pytest.raises(CustomSDKError, match="boom"):
        await client.get_prompt("summarize-doc", {"filename": "notes.md"})


@pytest.mark.anyio
async def test_awaits_sdk_call_exactly_once():
    fake_result = SimpleNamespace(messages=[])
    session = SimpleNamespace(get_prompt=AsyncMock(return_value=fake_result))
    client = make_client_with_session(session)

    await client.get_prompt("summarize-doc", {"filename": "notes.md"})

    assert session.get_prompt.await_count == 1


@pytest.mark.anyio
async def test_does_not_mutate_client_state():
    fake_result = SimpleNamespace(
        messages=[SimpleNamespace(role="user", content="hi")]
    )
    session = SimpleNamespace(get_prompt=AsyncMock(return_value=fake_result))
    client = make_client_with_session(session)

    session_before = client._session
    await client.get_prompt("summarize-doc", {"filename": "notes.md"})

    assert client._session is session_before
