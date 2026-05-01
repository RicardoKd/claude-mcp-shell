import os

from mcp.server.fastmcp import FastMCP

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


@mcp.tool()
def read_doc(filename: str) -> str:
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


@mcp.tool()
def create_doc(filename: str, content: str) -> str:
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


@mcp.tool()
def edit_doc(
    filename: str,
    old_str: str,
    new_str: str,
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


if __name__ == "__main__":
    mcp.run(transport="stdio")
