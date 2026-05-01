import os
import pytest

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import mcp_server
from mcp_server import edit_doc


@pytest.fixture(autouse=True)
def temp_docs_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(mcp_server, "DOCS_DIR", str(tmp_path))
    yield tmp_path


def test_happy_path_replaces_first_occurrence(temp_docs_dir):
    (temp_docs_dir / "notes.txt").write_text("hello world hello")
    result = edit_doc("notes.txt", "hello", "goodbye")
    assert result == "Document 'notes.txt' updated successfully."
    assert (temp_docs_dir / "notes.txt").read_text() == "goodbye world hello"


def test_happy_path_exact_whitespace_match(temp_docs_dir):
    (temp_docs_dir / "notes.txt").write_text("line one\nline two\nline three")
    result = edit_doc("notes.txt", "line two\nline three", "line TWO\nline THREE")
    assert result == "Document 'notes.txt' updated successfully."
    assert (temp_docs_dir / "notes.txt").read_text() == "line one\nline TWO\nline THREE"


def test_error_if_file_does_not_exist(temp_docs_dir):
    with pytest.raises(FileNotFoundError, match="Document 'missing.txt' does not exist."):
        edit_doc("missing.txt", "foo", "bar")


def test_error_if_old_str_not_found(temp_docs_dir):
    (temp_docs_dir / "notes.txt").write_text("hello world")
    with pytest.raises(ValueError, match="not found in document 'notes.txt'"):
        edit_doc("notes.txt", "nonexistent text", "replacement")


def test_return_value_wording(temp_docs_dir):
    (temp_docs_dir / "doc.md").write_text("original content")
    result = edit_doc("doc.md", "original content", "new content")
    assert result == "Document 'doc.md' updated successfully."


def test_only_first_occurrence_replaced(temp_docs_dir):
    (temp_docs_dir / "notes.txt").write_text("aaa aaa aaa")
    edit_doc("notes.txt", "aaa", "bbb")
    assert (temp_docs_dir / "notes.txt").read_text() == "bbb aaa aaa"
