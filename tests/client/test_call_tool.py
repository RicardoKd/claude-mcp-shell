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
async def test_happy_path_returns_sdk_call_tool_result():
    fake_result = SimpleNamespace(
        content=[SimpleNamespace(type="text", text="hello world")],
        isError=False,
    )
    session = SimpleNamespace(call_tool=AsyncMock(return_value=fake_result))
    client = make_client_with_session(session)

    result = await client.call_tool("read_doc", {"filename": "notes.txt"})

    assert result is fake_result
    session.call_tool.assert_awaited_once_with("read_doc", {"filename": "notes.txt"})


@pytest.mark.anyio
async def test_returns_none_when_sdk_returns_none():
    session = SimpleNamespace(call_tool=AsyncMock(return_value=None))
    client = make_client_with_session(session)

    result = await client.call_tool("read_doc", {"filename": "notes.txt"})

    assert result is None


@pytest.mark.anyio
async def test_raises_connection_error_when_not_connected():
    client = MCPClient(command="uv", args=["run", "mcp_server.py"])

    with pytest.raises(ConnectionError):
        await client.call_tool("read_doc", {"filename": "notes.txt"})


@pytest.mark.anyio
async def test_propagates_sdk_exception_unchanged():
    class CustomSDKError(Exception):
        pass

    session = SimpleNamespace(
        call_tool=AsyncMock(side_effect=CustomSDKError("boom"))
    )
    client = make_client_with_session(session)

    with pytest.raises(CustomSDKError, match="boom"):
        await client.call_tool("read_doc", {"filename": "notes.txt"})


@pytest.mark.anyio
async def test_tool_input_passed_through_as_is():
    fake_result = SimpleNamespace(content=[], isError=False)
    session = SimpleNamespace(call_tool=AsyncMock(return_value=fake_result))
    client = make_client_with_session(session)

    tool_input = {"filename": "report.md", "extra": {"nested": [1, 2, 3]}}
    await client.call_tool("edit_doc", tool_input)

    session.call_tool.assert_awaited_once_with("edit_doc", tool_input)
    # Verify the exact same dict object was passed (not copied/re-keyed)
    call_args = session.call_tool.await_args
    assert call_args.args[1] is tool_input


@pytest.mark.anyio
async def test_empty_dict_tool_input_passed_through():
    fake_result = SimpleNamespace(content=[], isError=False)
    session = SimpleNamespace(call_tool=AsyncMock(return_value=fake_result))
    client = make_client_with_session(session)

    await client.call_tool("some_tool", {})

    session.call_tool.assert_awaited_once_with("some_tool", {})
