import datetime
import json
import mimetypes
import os

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base
from pydantic import Field

from core import doc_store
from core.doc_store import check_binary, doc_path, exists, is_binary, require_exists

mcp = FastMCP("DocumentMCP", log_level="ERROR")


@mcp.tool(
    name="read_doc",
    description="Read and return the contents of a document from the document store.",
)
def read_doc(
    filename: str = Field(
        description="Filename of the document to read (e.g. 'notes.txt', 'report.md')."
    ),
) -> str:
    path = require_exists(filename)
    with open(path, "r") as f:
        return f.read()


@mcp.tool(
    name="create_doc",
    description="Create a new document in the document store with the given content.",
)
def create_doc(
    filename: str = Field(
        description="Filename for the new document (e.g. 'notes.txt', 'report.md'). Must not already exist."
    ),
    content: str = Field(description="Text content to write into the new document."),
) -> str:
    path = doc_path(filename)
    if os.path.exists(path):
        raise FileExistsError(f"Document '{filename}' already exists.")

    os.makedirs(doc_store.DOCS_DIR, exist_ok=True)
    with open(path, "w") as f:
        f.write(content)

    return f"Document '{filename}' created successfully."


@mcp.tool(
    name="edit_doc",
    description="Replace the first exact occurrence of a string in a document with new text.",
)
def edit_doc(
    filename: str = Field(description="Filename of the document to edit."),
    old_str: str = Field(
        description="The text to replace. Must match exactly, including whitespace."
    ),
    new_str: str = Field(
        description="The new text to insert in place of the old text."
    ),
) -> str:
    path = require_exists(filename)
    with open(path, "r") as f:
        content = f.read()

    if old_str not in content:
        raise ValueError(f"'{old_str}' not found in document '{filename}'.")

    updated = content.replace(old_str, new_str, 1)
    with open(path, "w") as f:
        f.write(updated)

    return f"Document '{filename}' updated successfully."


@mcp.tool(
    name="delete_doc",
    description="Permanently delete a document from the document store.",
)
def delete_doc(
    filename: str = Field(description="Filename of the document to delete."),
) -> str:
    path = require_exists(filename)
    os.remove(path)
    return f"Document '{filename}' deleted successfully."


@mcp.resource(
    "docs://list",
    mime_type="application/json",
    description="List metadata for all supported (non-binary) documents in the document store.",
)
def list_docs() -> str:
    docs_dir = doc_store.DOCS_DIR
    entries = []
    if os.path.isdir(docs_dir):
        for filename in os.listdir(docs_dir):
            if is_binary(filename):
                continue
            path = os.path.join(docs_dir, filename)
            if not os.path.isfile(path):
                continue
            stat = os.stat(path)
            updated_at = datetime.datetime.fromtimestamp(
                stat.st_mtime, tz=datetime.timezone.utc
            ).strftime("%Y-%m-%dT%H:%M:%SZ")
            mime_type, _ = mimetypes.guess_type(filename)
            entries.append(
                {
                    "filename": filename,
                    "size_bytes": stat.st_size,
                    "updated_at": updated_at,
                    "mime_type": mime_type or "text/plain",
                }
            )

    entries.sort(key=lambda e: e["filename"])
    return json.dumps(entries)


@mcp.resource(
    "docs://{filename}",
    mime_type="text/plain",
    description="Return the content of a document as plain text for embedding in model context.",
)
def read_doc_resource(filename: str) -> str:
    path = require_exists(filename)
    with open(path, "r") as f:
        return f.read()


@mcp.prompt(
    name="rewrite-as-markdown",
    description="Rewrites the contents of a document in Markdown format.",
)
def rewrite_as_markdown(
    filename: str = Field(description="Filename of the document to rewrite."),
) -> list[base.Message]:
    check_binary(filename)
    if not exists(filename):
        return [
            base.UserMessage(
                f"The document '{filename}' does not exist. To create it, you could prompt: 'Create a new document called {filename} with the following content: ...'"
            )
        ]

    prompt = f"""
        Fetch the contents of the document <filename>{filename}</filename> via the
        `docs://{filename}` resource. Reformat the content using Markdown syntax —
        add headers, bullet points, tables, and other structure as appropriate.
        Then apply the rewrite by calling the `edit_doc` tool on
        <filename>{filename}</filename>, replacing the original text with the new
        Markdown-formatted version.
    """

    return [base.UserMessage(prompt)]


@mcp.prompt(
    name="summarize-doc",
    description="Summarizes the contents of a document.",
)
def summarize_doc(
    filename: str = Field(description="Filename of the document to summarize."),
) -> list[base.Message]:
    check_binary(filename)
    if not exists(filename):
        return [
            base.UserMessage(
                f"The document '{filename}' does not exist. To create it, you could prompt: 'Create a new document called {filename} with the following content: ...'"
            )
        ]

    prompt = f"""
        Fetch the contents of the document <filename>{filename}</filename> via the
        `docs://{filename}` resource. Produce a concise summary of the content of
        <filename>{filename}</filename>, capturing the key points and main ideas.
    """

    return [base.UserMessage(prompt)]


if __name__ == "__main__":
    mcp.run(transport="stdio")
