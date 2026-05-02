import os

DOCS_DIR = "docs"
BINARY_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt",
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg", ".ico",
    ".zip", ".tar", ".gz", ".rar", ".7z",
    ".mp3", ".mp4", ".avi", ".mov", ".wav",
    ".exe", ".dll", ".so", ".dylib",
    ".db", ".sqlite",
}


def check_binary(filename: str) -> None:
    _, ext = os.path.splitext(filename)
    if ext.lower() in BINARY_EXTENSIONS:
        raise ValueError(
            f"'{filename}' is a binary format and is not supported. Use a plain text format such as .md or .txt."
        )


def doc_path(filename: str) -> str:
    if os.path.basename(filename) != filename or filename.startswith("."):
        raise ValueError(f"Invalid filename: '{filename}'.")
    check_binary(filename)
    return os.path.join(DOCS_DIR, filename)


def require_exists(filename: str) -> str:
    path = doc_path(filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Document '{filename}' does not exist.")
    return path
