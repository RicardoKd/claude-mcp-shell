import os
import pytest

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core import doc_store
from mcp_server import delete_doc


@pytest.fixture(autouse=True)
def temp_docs_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(doc_store, "DOCS_DIR", str(tmp_path))
    yield tmp_path


def test_happy_path_deletes_file(temp_docs_dir):
    (temp_docs_dir / "notes.txt").write_text("some content")
    result = delete_doc("notes.txt")
    assert result == "Document 'notes.txt' deleted successfully."
    assert not (temp_docs_dir / "notes.txt").exists()


def test_error_if_file_does_not_exist(temp_docs_dir):
    with pytest.raises(FileNotFoundError, match="Document 'missing.txt' does not exist."):
        delete_doc("missing.txt")


def test_error_on_path_traversal(temp_docs_dir):
    with pytest.raises(ValueError, match="Invalid filename"):
        delete_doc("../evil.txt")


def test_error_on_absolute_path(temp_docs_dir):
    with pytest.raises(ValueError, match="Invalid filename"):
        delete_doc("/etc/passwd")


def test_error_on_hidden_file(temp_docs_dir):
    with pytest.raises(ValueError, match="Invalid filename"):
        delete_doc(".hidden")
