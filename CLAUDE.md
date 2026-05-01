# Claude MCP Shell

## Project Overview

An MCP server and CLI chat interface for Claude, implementing tools, resources, and prompts through a document store.

## Document Store

Documents are stored as individual files in a `docs/` directory on disk. The server reads from and writes to this directory directly. There is no in-memory dict — all operations go to the filesystem.

Filenames (e.g. `notes.txt`, `deposition.md`) serve as the document identifier throughout. The term "filename" is used consistently in all code and user-facing descriptions.

**Supported formats:** plain text files only (e.g. `.md`, `.txt`, `.json`, `.csv`). Binary formats (`.pdf`, `.docx`, etc.) are not supported. Any tool or resource that attempts to read or write a binary file must raise an error: `"'{filename}' is a binary format and is not supported. Use a plain text format such as .md or .txt."`

## Tools

All tools are registered with an explicit `name` and `description` on `@mcp.tool()`, and every argument uses `Field(description="...")` from Pydantic.

### `read_doc`

```python
@mcp.tool(
    name="read_doc",
    description="Read and return the contents of a document from the document store.",
)
def read_doc(
    filename: str = Field(description="Filename of the document to read (e.g. 'notes.txt', 'report.md')."),
) -> str
```

- Read and return the content of `docs/{filename}`.
- Raise an error if the file does not exist.
- **Purpose:** programmatic access within agentic workflows.

### `create_doc`

```python
@mcp.tool(
    name="create_doc",
    description="Create a new document in the document store with the given content.",
)
def create_doc(
    filename: str = Field(description="Filename for the new document (e.g. 'notes.txt', 'report.md'). Must not already exist."),
    content: str = Field(description="Text content to write into the new document."),
) -> str
```

- Create a new file at `docs/{filename}` with the given content.
- Raise an error if the file already exists.
- Return a confirmation string on success.

### `edit_doc`

```python
@mcp.tool(
    name="edit_doc",
    description="Replace the first exact occurrence of a string in a document with new text.",
)
def edit_doc(
    filename: str = Field(description="Filename of the document to edit."),
    old_str: str = Field(description="The text to replace. Must match exactly, including whitespace."),
    new_str: str = Field(description="The new text to insert in place of the old text."),
) -> str
```

- Replace the first exact occurrence of `old_str` with `new_str` in `docs/{filename}`.
- Raise an error if the file does not exist or if `old_str` is not found.
- Return: `"Document '{filename}' updated successfully."`

### `delete_doc`

```python
@mcp.tool(
    name="delete_doc",
    description="Permanently delete a document from the document store.",
)
def delete_doc(
    filename: str = Field(description="Filename of the document to delete."),
) -> str
```

- Remove `docs/{filename}` from disk.
- Raise an error if the file does not exist.
- Return a confirmation string on success.

## Resources

### `docs://list`

- Reads the `docs/` directory on disk.
- Returns all filenames as newline-separated plain text: `"deposition.md\nreport.pdf\n..."`

### `docs://{filename}`

- Return the content of `docs/{filename}`.
- Raise an error if the file does not exist.
- **Purpose:** embedding document content directly into model context.

> Both `read_doc` (tool) and `docs://{filename}` (resource) return doc content. The distinction is intentional: the resource is for embedding content into model context; the tool is for programmatic access in agentic workflows.

## Prompts

### `rewrite-as-markdown`

```python
def rewrite_as_markdown(filename: str)
```

- Read the content of `docs/{filename}`.
- If the file does not exist, return: `"The document '{filename}' does not exist. To create it, you could prompt: 'Create a new document called {filename} with the following content: ...'"`
- Otherwise return a prompt asking the model to rewrite the content in markdown format.

### `summarize_doc`

```python
def summarize_doc(filename: str)
```

- Read the content of `docs/{filename}`.
- If the file does not exist, return: `"The document '{filename}' does not exist. To create it, you could prompt: 'Create a new document called {filename} with the following content: ...'"`
- Otherwise return a prompt asking the model to summarize the content.
