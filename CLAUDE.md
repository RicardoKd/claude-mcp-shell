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

## MCP Client Implementation

`MCPClient` (in `mcp_client.py`) wraps an MCP `ClientSession` and exposes typed async methods over it. All implementations follow these invariants:

- Every method acquires the session through `self.session()`, which raises `ConnectionError` if `connect()` has not been called.
- Every method is `async` and `await`s the underlying SDK call exactly once.
- SDK return types are returned directly. The client must not catch, remap, or repackage server-side errors — they propagate as `McpError` to the caller.
- No method mutates client state.

### `list_tools() -> list[types.Tool]`

- `result = await self.session().list_tools()`
- Return `result.tools`.

### `call_tool(tool_name: str, tool_input: dict) -> types.CallToolResult | None`

- Return `await self.session().call_tool(tool_name, tool_input)`.
- Pass `tool_input` as-is to the SDK's `arguments` parameter; do not copy, validate, or re-key.
- Return value is whatever the SDK returns; `None` is preserved only if the SDK returns it.

### `list_prompts() -> list[types.Prompt]`

- `result = await self.session().list_prompts()`
- Return `result.prompts`.

### `get_prompt(prompt_name: str, args: dict[str, str]) -> list[types.PromptMessage]`

- Update the annotation to `-> list[types.PromptMessage]`.
- `result = await self.session().get_prompt(prompt_name, args)`
- Return `result.messages`.

### `read_resource(uri: str) -> Any`

- `result = await self.session().read_resource(uri)`
- Read the first item: `content = result.contents[0]`. The server only ever returns a single content item for `docs://list` and `docs://{filename}`.
- If `content.mimeType == "application/json"`, return `json.loads(content.text)`.
- Otherwise return `content.text` unchanged.
- Add `import json` to the module imports.
- Binary (`BlobResourceContents`) is never expected because the server rejects binary filenames; no special handling is required.

### Out of scope

- Retries, timeouts, logging, caching, and reconnection are explicitly excluded — the SDK and the existing `AsyncExitStack` lifecycle handle these.
