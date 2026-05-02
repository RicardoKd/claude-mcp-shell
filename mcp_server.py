import os

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from core import doc_store
from core.doc_store import doc_path, require_exists

mcp = FastMCP("DocumentMCP", log_level="ERROR")


@mcp.tool(
    name="read_doc",
    description="Read and return the contents of a document from the document store.",
)
def read_doc(
    filename: str = Field(description="Filename of the document to read (e.g. 'notes.txt', 'report.md')."),
) -> str:
    path = require_exists(filename)
    with open(path, "r") as f:
        return f.read()


@mcp.tool(
    name="create_doc",
    description="Create a new document in the document store with the given content.",
)
def create_doc(
    filename: str = Field(description="Filename for the new document (e.g. 'notes.txt', 'report.md'). Must not already exist."),
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
    old_str: str = Field(description="The text to replace. Must match exactly, including whitespace."),
    new_str: str = Field(description="The new text to insert in place of the old text."),
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


if __name__ == "__main__":
    mcp.run(transport="stdio")
