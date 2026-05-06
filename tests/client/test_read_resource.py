import json
import os
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from mcp import types
from pydantic import AnyUrl

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from mcp_client import MCPClient


@pytest.fixture
def anyio_backend():
    return "asyncio"


def make_client_with_session(session):
    client = MCPClient(command="uv", args=["run", "mcp_server.py"])
    client._session = session
    return client


def make_text_resource(uri: str, mime_type: str, text: str) -> types.TextResourceContents:
    return types.TextResourceContents(uri=AnyUrl(uri), mimeType=mime_type, text=text)


@pytest.mark.anyio
async def test_json_mimetype_returns_parsed_json():
    payload = [{"filename": "notes.md", "size_bytes": 42}]
    resource = make_text_resource("docs://list", "application/json", json.dumps(payload))
    fake_result = SimpleNamespace(contents=[resource])
    session = SimpleNamespace(read_resource=AsyncMock(return_value=fake_result))
    client = make_client_with_session(session)

    result = await client.read_resource("docs://list")

    assert result == payload


@pytest.mark.anyio
async def test_text_mimetype_returns_text_unchanged():
    resource = make_text_resource("docs://notes.md", "text/plain", "raw body")
    fake_result = SimpleNamespace(contents=[resource])
    session = SimpleNamespace(read_resource=AsyncMock(return_value=fake_result))
    client = make_client_with_session(session)

    result = await client.read_resource("docs://notes.md")

    assert result == "raw body"


@pytest.mark.anyio
async def test_non_text_resource_returns_none():
    blob_like = SimpleNamespace(
        uri="docs://opaque", mimeType="application/octet-stream", blob="..."
    )
    fake_result = SimpleNamespace(contents=[blob_like])
    session = SimpleNamespace(read_resource=AsyncMock(return_value=fake_result))
    client = make_client_with_session(session)

    result = await client.read_resource("docs://opaque")

    assert result is None


@pytest.mark.anyio
async def test_raises_connection_error_when_not_connected():
    client = MCPClient(command="uv", args=["run", "mcp_server.py"])

    with pytest.raises(ConnectionError):
        await client.read_resource("docs://list")


@pytest.mark.anyio
async def test_propagates_sdk_exception_unchanged():
    class CustomSDKError(Exception):
        pass

    session = SimpleNamespace(
        read_resource=AsyncMock(side_effect=CustomSDKError("boom"))
    )
    client = make_client_with_session(session)

    with pytest.raises(CustomSDKError, match="boom"):
        await client.read_resource("docs://list")


@pytest.mark.anyio
async def test_uri_wrapped_in_anyurl():
    resource = make_text_resource("docs://list", "text/plain", "x")
    fake_result = SimpleNamespace(contents=[resource])
    session = SimpleNamespace(read_resource=AsyncMock(return_value=fake_result))
    client = make_client_with_session(session)

    await client.read_resource("docs://list")

    session.read_resource.assert_awaited_once_with(AnyUrl("docs://list"))
