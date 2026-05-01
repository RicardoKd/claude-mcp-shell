import os
import pytest

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import mcp_server
from mcp_server import read_doc


@pytest.fixture(autouse=True)
def temp_docs_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(mcp_server, "DOCS_DIR", str(tmp_path))
    yield tmp_path


def test_happy_path_returns_content(temp_docs_dir):
    (temp_docs_dir / "notes.txt").write_text("hello world")
    assert read_doc("notes.txt") == "hello world"


def test_happy_path_md_file(temp_docs_dir):
    (temp_docs_dir / "report.md").write_text("# Title\nBody text")
    assert read_doc("report.md") == "# Title\nBody text"


def test_error_if_file_does_not_exist(temp_docs_dir):
    with pytest.raises(FileNotFoundError, match="Document 'missing.txt' does not exist."):
        read_doc("missing.txt")


def test_error_on_binary_pdf(temp_docs_dir):
    with pytest.raises(ValueError, match="'report.pdf' is a binary format and is not supported. Use a plain text format such as .md or .txt."):
        read_doc("report.pdf")


def test_error_on_binary_docx(temp_docs_dir):
    with pytest.raises(ValueError, match="'file.docx' is a binary format and is not supported. Use a plain text format such as .md or .txt."):
        read_doc("file.docx")


def test_binary_check_is_case_insensitive(temp_docs_dir):
    with pytest.raises(ValueError, match="is a binary format"):
        read_doc("FILE.PDF")


def test_error_on_path_traversal(temp_docs_dir):
    with pytest.raises(ValueError, match="Invalid filename"):
        read_doc("../evil.txt")


def test_error_on_absolute_path(temp_docs_dir):
    with pytest.raises(ValueError, match="Invalid filename"):
        read_doc("/etc/passwd")


def test_error_on_hidden_file(temp_docs_dir):
    with pytest.raises(ValueError, match="Invalid filename"):
        read_doc(".hidden")
