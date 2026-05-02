import os
import pytest

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core import doc_store
from mcp_server import read_doc_resource, mcp


@pytest.fixture(autouse=True)
def temp_docs_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(doc_store, "DOCS_DIR", str(tmp_path))
    yield tmp_path


def test_happy_path_returns_content(temp_docs_dir):
    (temp_docs_dir / "notes.txt").write_text("hello world")
    assert read_doc_resource("notes.txt") == "hello world"


def test_error_if_file_does_not_exist(temp_docs_dir):
    with pytest.raises(FileNotFoundError, match="Document 'missing.txt' does not exist."):
        read_doc_resource("missing.txt")


def test_error_on_binary_extension(temp_docs_dir):
    with pytest.raises(
        ValueError,
        match="'report.pdf' is a binary format and is not supported. Use a plain text format such as .md or .txt.",
    ):
        read_doc_resource("report.pdf")


def test_md_file_returned_as_plain_text(temp_docs_dir):
    (temp_docs_dir / "report.md").write_text("# Title\nBody")
    assert read_doc_resource("report.md") == "# Title\nBody"


def test_json_file_returned_as_plain_text(temp_docs_dir):
    (temp_docs_dir / "data.json").write_text('{"k": 1}')
    assert read_doc_resource("data.json") == '{"k": 1}'


def test_csv_file_returned_as_plain_text(temp_docs_dir):
    (temp_docs_dir / "data.csv").write_text("a,b\n1,2")
    assert read_doc_resource("data.csv") == "a,b\n1,2"


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_resource_registered_with_text_plain_mime_type():
    templates = await mcp.list_resource_templates()
    matches = [t for t in templates if t.uriTemplate == "docs://{filename}"]
    assert len(matches) == 1
    assert matches[0].mimeType == "text/plain"
