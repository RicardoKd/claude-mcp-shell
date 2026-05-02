import os
import pytest

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import mcp_server
from mcp_server import create_doc


@pytest.fixture(autouse=True)
def temp_docs_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(mcp_server, "DOCS_DIR", str(tmp_path))
    yield tmp_path


def test_happy_path_creates_file(temp_docs_dir):
    result = create_doc("notes.txt", "hello world")
    assert result == "Document 'notes.txt' created successfully."
    assert (temp_docs_dir / "notes.txt").read_text() == "hello world"


def test_happy_path_md_file(temp_docs_dir):
    result = create_doc("report.md", "# Title\nBody text")
    assert result == "Document 'report.md' created successfully."
    assert (temp_docs_dir / "report.md").read_text() == "# Title\nBody text"


def test_error_if_file_already_exists(temp_docs_dir):
    (temp_docs_dir / "notes.txt").write_text("existing")
    with pytest.raises(FileExistsError, match="Document 'notes.txt' already exists."):
        create_doc("notes.txt", "new content")


def test_error_on_binary_pdf(temp_docs_dir):
    with pytest.raises(ValueError, match="'report.pdf' is a binary format and is not supported. Use a plain text format such as .md or .txt."):
        create_doc("report.pdf", "some content")


def test_error_on_binary_docx(temp_docs_dir):
    with pytest.raises(ValueError, match="'file.docx' is a binary format and is not supported. Use a plain text format such as .md or .txt."):
        create_doc("file.docx", "some content")


def test_binary_check_is_case_insensitive(temp_docs_dir):
    with pytest.raises(ValueError, match="is a binary format"):
        create_doc("FILE.PDF", "some content")


def test_error_on_path_traversal(temp_docs_dir):
    with pytest.raises(ValueError, match="Invalid filename"):
        create_doc("../evil.txt", "content")


def test_error_on_absolute_path(temp_docs_dir):
    with pytest.raises(ValueError, match="Invalid filename"):
        create_doc("/etc/passwd", "content")


def test_error_on_hidden_file(temp_docs_dir):
    with pytest.raises(ValueError, match="Invalid filename"):
        create_doc(".hidden", "content")


def test_creates_docs_dir_if_missing(tmp_path, monkeypatch):
    docs_path = tmp_path / "newdocs"
    monkeypatch.setattr(mcp_server, "DOCS_DIR", str(docs_path))
    result = create_doc("notes.txt", "content")
    assert result == "Document 'notes.txt' created successfully."
    assert (docs_path / "notes.txt").read_text() == "content"
