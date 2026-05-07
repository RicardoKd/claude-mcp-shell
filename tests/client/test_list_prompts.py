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
async def test_happy_path_returns_prompts_list():
    fake_prompt_a = SimpleNamespace(name="rewrite-as-markdown")
    fake_prompt_b = SimpleNamespace(name="summarize-doc")
    fake_result = SimpleNamespace(prompts=[fake_prompt_a, fake_prompt_b])

    session = SimpleNamespace(list_prompts=AsyncMock(return_value=fake_result))
    client = make_client_with_session(session)

    prompts = await client.list_prompts()

    assert prompts == [fake_prompt_a, fake_prompt_b]
    session.list_prompts.assert_awaited_once_with()


@pytest.mark.anyio
async def test_returns_prompts_attribute_not_full_result():
    fake_prompt = SimpleNamespace(name="rewrite-as-markdown")
    fake_result = SimpleNamespace(prompts=[fake_prompt])

    session = SimpleNamespace(list_prompts=AsyncMock(return_value=fake_result))
    client = make_client_with_session(session)

    result = await client.list_prompts()

    # Must return result.prompts, not the whole result object.
    assert result is not fake_result
    assert result == [fake_prompt]


@pytest.mark.anyio
async def test_returns_empty_list_when_no_prompts():
    fake_result = SimpleNamespace(prompts=[])

    session = SimpleNamespace(list_prompts=AsyncMock(return_value=fake_result))
    client = make_client_with_session(session)

    prompts = await client.list_prompts()

    assert prompts == []
    session.list_prompts.assert_awaited_once_with()


@pytest.mark.anyio
async def test_raises_connection_error_when_not_connected():
    client = MCPClient(command="uv", args=["run", "mcp_server.py"])

    with pytest.raises(ConnectionError):
        await client.list_prompts()


@pytest.mark.anyio
async def test_propagates_sdk_exception_unchanged():
    class CustomSDKError(Exception):
        pass

    session = SimpleNamespace(
        list_prompts=AsyncMock(side_effect=CustomSDKError("boom"))
    )
    client = make_client_with_session(session)

    with pytest.raises(CustomSDKError, match="boom"):
        await client.list_prompts()


@pytest.mark.anyio
async def test_awaits_sdk_call_exactly_once():
    fake_result = SimpleNamespace(prompts=[])
    session = SimpleNamespace(list_prompts=AsyncMock(return_value=fake_result))
    client = make_client_with_session(session)

    await client.list_prompts()

    assert session.list_prompts.await_count == 1


@pytest.mark.anyio
async def test_does_not_mutate_client_state():
    fake_result = SimpleNamespace(prompts=[SimpleNamespace(name="summarize-doc")])
    session = SimpleNamespace(list_prompts=AsyncMock(return_value=fake_result))
    client = make_client_with_session(session)

    session_before = client._session
    await client.list_prompts()

    assert client._session is session_before
