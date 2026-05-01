import os

from mcp.server.fastmcp import FastMCP
from pydantic import Field

DOCS_DIR = "docs"
BINARY_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt",
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg", ".ico",
    ".zip", ".tar", ".gz", ".rar", ".7z",
    ".mp3", ".mp4", ".avi", ".mov", ".wav",
    ".exe", ".dll", ".so", ".dylib",
    ".db", ".sqlite",
}

mcp = FastMCP("DocumentMCP", log_level="ERROR")


@mcp.tool(
    name="read_doc",
    description="Read and return the contents of a document from the document store.",
)
def read_doc(
    filename: str = Field(description="Filename of the document to read (e.g. 'notes.txt', 'report.md')."),
) -> str:
    _, ext = os.path.splitext(filename)
    if ext.lower() in BINARY_EXTENSIONS:
        raise ValueError(
            f"'{filename}' is a binary format and is not supported. Use a plain text format such as .md or .txt."
        )

    path = os.path.join(DOCS_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Document '{filename}' does not exist.")

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
    if os.path.basename(filename) != filename or filename.startswith("."):
        raise ValueError(f"Invalid filename: '{filename}'.")

    _, ext = os.path.splitext(filename)
    if ext.lower() in BINARY_EXTENSIONS:
        raise ValueError(
            f"'{filename}' is a binary format and is not supported. Use a plain text format such as .md or .txt."
        )

    path = os.path.join(DOCS_DIR, filename)
    if os.path.exists(path):
        raise FileExistsError(f"Document '{filename}' already exists.")

    os.makedirs(DOCS_DIR, exist_ok=True)
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
    path = os.path.join(DOCS_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Document '{filename}' does not exist.")

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
    path = os.path.join(DOCS_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Document '{filename}' does not exist.")

    os.remove(path)
    return f"Document '{filename}' deleted successfully."


if __name__ == "__main__":
    mcp.run(transport="stdio")
