import os
import pytest

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from mcp.server.fastmcp.prompts import base

from core import doc_store
from mcp_server import summarize_doc, mcp


@pytest.fixture(autouse=True)
def temp_docs_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(doc_store, "DOCS_DIR", str(tmp_path))
    yield tmp_path


def test_happy_path_returns_single_user_message(temp_docs_dir):
    (temp_docs_dir / "notes.md").write_text("hello world")

    messages = summarize_doc("notes.md")

    assert isinstance(messages, list)
    assert len(messages) == 1
    assert isinstance(messages[0], base.UserMessage)
    assert messages[0].role == "user"


def test_happy_path_prompt_body_contains_required_references(temp_docs_dir):
    (temp_docs_dir / "notes.md").write_text("hello world")

    messages = summarize_doc("notes.md")
    body = messages[0].content.text

    assert "<filename>notes.md</filename>" in body
    assert "docs://notes.md" in body


def test_happy_path_with_txt_file(temp_docs_dir):
    (temp_docs_dir / "report.txt").write_text("some content")

    messages = summarize_doc("report.txt")
    body = messages[0].content.text

    assert "<filename>report.txt</filename>" in body
    assert "docs://report.txt" in body


def test_missing_file_returns_helpful_user_message(temp_docs_dir):
    messages = summarize_doc("missing.md")

    assert len(messages) == 1
    assert isinstance(messages[0], base.UserMessage)
    assert messages[0].content.text == (
        "The document 'missing.md' does not exist. To create it, you could prompt: "
        "'Create a new document called missing.md with the following content: ...'"
    )


def test_missing_file_does_not_raise(temp_docs_dir):
    # Should not raise FileNotFoundError — missing-file is a prompt body, not an exception.
    summarize_doc("nope.txt")


def test_binary_extension_raises_standard_error(temp_docs_dir):
    with pytest.raises(
        ValueError,
        match="'report.pdf' is a binary format and is not supported. Use a plain text format such as .md or .txt.",
    ):
        summarize_doc("report.pdf")


def test_binary_extension_raises_even_when_file_exists(temp_docs_dir):
    # check_binary must run before exists — error should fire regardless of presence.
    (temp_docs_dir / "image.png").write_bytes(b"\x89PNG")
    with pytest.raises(ValueError, match="is a binary format"):
        summarize_doc("image.png")


def test_binary_check_runs_before_exists_check(temp_docs_dir):
    # Binary file that does not exist must still raise the binary error,
    # not return the missing-file UserMessage.
    with pytest.raises(ValueError, match="is a binary format"):
        summarize_doc("missing.docx")


def test_binary_check_is_case_insensitive(temp_docs_dir):
    with pytest.raises(ValueError, match="is a binary format"):
        summarize_doc("FILE.PDF")


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_prompt_registration_metadata():
    prompts = await mcp.list_prompts()
    matches = [p for p in prompts if p.name == "summarize-doc"]
    assert len(matches) == 1
    assert matches[0].description == "Summarizes the contents of a document."


@pytest.mark.anyio
async def test_prompt_argument_metadata():
    prompts = await mcp.list_prompts()
    prompt = next(p for p in prompts if p.name == "summarize-doc")
    assert prompt.arguments is not None
    arg_names = [a.name for a in prompt.arguments]
    assert arg_names == ["filename"]
    filename_arg = prompt.arguments[0]
    assert filename_arg.required is True
    assert filename_arg.description == "Filename of the document to summarize."
