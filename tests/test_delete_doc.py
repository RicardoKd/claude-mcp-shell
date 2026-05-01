import os
import pytest

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import mcp_server
from mcp_server import delete_doc


@pytest.fixture(autouse=True)
def temp_docs_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(mcp_server, "DOCS_DIR", str(tmp_path))
    yield tmp_path


def test_happy_path_deletes_file(temp_docs_dir):
    (temp_docs_dir / "notes.txt").write_text("some content")
    result = delete_doc("notes.txt")
    assert result == "Document 'notes.txt' deleted successfully."
    assert not (temp_docs_dir / "notes.txt").exists()


def test_error_if_file_does_not_exist(temp_docs_dir):
    with pytest.raises(FileNotFoundError, match="Document 'missing.txt' does not exist."):
        delete_doc("missing.txt")
