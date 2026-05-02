import json
import os
import re
import pytest

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core import doc_store
from mcp_server import list_docs, mcp


@pytest.fixture(autouse=True)
def temp_docs_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(doc_store, "DOCS_DIR", str(tmp_path))
    yield tmp_path


def test_happy_path_returns_json_list(temp_docs_dir):
    (temp_docs_dir / "notes.txt").write_text("hello")
    result = list_docs()
    parsed = json.loads(result)
    assert isinstance(parsed, list)
    assert len(parsed) == 1
    assert parsed[0]["filename"] == "notes.txt"


def test_empty_directory_returns_empty_list(temp_docs_dir):
    assert json.loads(list_docs()) == []


def test_missing_directory_returns_empty_list(tmp_path, monkeypatch):
    missing = tmp_path / "nonexistent"
    monkeypatch.setattr(doc_store, "DOCS_DIR", str(missing))
    assert json.loads(list_docs()) == []


def test_sort_order_ascending(temp_docs_dir):
    (temp_docs_dir / "charlie.txt").write_text("c")
    (temp_docs_dir / "alpha.txt").write_text("a")
    (temp_docs_dir / "bravo.md").write_text("b")
    parsed = json.loads(list_docs())
    assert [e["filename"] for e in parsed] == ["alpha.txt", "bravo.md", "charlie.txt"]


def test_binary_files_skipped(temp_docs_dir):
    (temp_docs_dir / "notes.txt").write_text("text")
    (temp_docs_dir / "report.pdf").write_text("fakepdf")
    (temp_docs_dir / "image.png").write_text("fakeimg")
    (temp_docs_dir / "doc.docx").write_text("fakedoc")
    parsed = json.loads(list_docs())
    filenames = [e["filename"] for e in parsed]
    assert filenames == ["notes.txt"]


def test_binary_skip_is_case_insensitive(temp_docs_dir):
    (temp_docs_dir / "notes.txt").write_text("text")
    (temp_docs_dir / "REPORT.PDF").write_text("fake")
    parsed = json.loads(list_docs())
    assert [e["filename"] for e in parsed] == ["notes.txt"]


def test_updated_at_format(temp_docs_dir):
    (temp_docs_dir / "notes.txt").write_text("hello")
    parsed = json.loads(list_docs())
    updated_at = parsed[0]["updated_at"]
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", updated_at), \
        f"Got: {updated_at}"
    assert "+00:00" not in updated_at
    assert "." not in updated_at


def test_all_four_fields_present(temp_docs_dir):
    (temp_docs_dir / "notes.md").write_text("hello")
    parsed = json.loads(list_docs())
    entry = parsed[0]
    assert set(entry.keys()) == {"filename", "size_bytes", "updated_at", "mime_type"}


def test_size_bytes_correct(temp_docs_dir):
    content = "hello world"
    (temp_docs_dir / "notes.txt").write_text(content)
    parsed = json.loads(list_docs())
    assert parsed[0]["size_bytes"] == len(content)


def test_mime_type_md(temp_docs_dir):
    (temp_docs_dir / "report.md").write_text("# title")
    parsed = json.loads(list_docs())
    assert parsed[0]["mime_type"] == "text/markdown"


def test_mime_type_txt(temp_docs_dir):
    (temp_docs_dir / "notes.txt").write_text("text")
    parsed = json.loads(list_docs())
    assert parsed[0]["mime_type"] == "text/plain"


def test_mime_type_json(temp_docs_dir):
    (temp_docs_dir / "data.json").write_text("{}")
    parsed = json.loads(list_docs())
    assert parsed[0]["mime_type"] == "application/json"


def test_mime_type_csv(temp_docs_dir):
    (temp_docs_dir / "data.csv").write_text("a,b")
    parsed = json.loads(list_docs())
    assert parsed[0]["mime_type"] == "text/csv"


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_resource_registered_with_correct_mime_type():
    resources = await mcp.list_resources()
    matches = [r for r in resources if str(r.uri) == "docs://list"]
    assert len(matches) == 1
    assert matches[0].mimeType == "application/json"
