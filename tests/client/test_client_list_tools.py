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
async def test_happy_path_returns_tools_list():
    fake_tool_a = SimpleNamespace(name="read_doc")
    fake_tool_b = SimpleNamespace(name="create_doc")
    fake_result = SimpleNamespace(tools=[fake_tool_a, fake_tool_b])

    session = SimpleNamespace(list_tools=AsyncMock(return_value=fake_result))
    client = make_client_with_session(session)

    tools = await client.list_tools()

    assert tools == [fake_tool_a, fake_tool_b]
    session.list_tools.assert_awaited_once_with()


@pytest.mark.anyio
async def test_raises_connection_error_when_not_connected():
    client = MCPClient(command="uv", args=["run", "mcp_server.py"])

    with pytest.raises(ConnectionError):
        await client.list_tools()


@pytest.mark.anyio
async def test_propagates_sdk_exception_unchanged():
    class CustomSDKError(Exception):
        pass

    session = SimpleNamespace(
        list_tools=AsyncMock(side_effect=CustomSDKError("boom"))
    )
    client = make_client_with_session(session)

    with pytest.raises(CustomSDKError, match="boom"):
        await client.list_tools()
