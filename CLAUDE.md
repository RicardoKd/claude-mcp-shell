# Claude MCP Shell

## Project Overview

An MCP server and CLI chat interface for Claude, implementing tools, resources, and prompts through a document store.

## Document Store

Documents are stored as individual files in a `docs/` directory on disk. The server reads from and writes to this directory directly. There is no in-memory dict — all operations go to the filesystem.

Filenames (e.g. `notes.txt`, `deposition.md`) serve as the document identifier throughout. The term "filename" is used consistently in all code and user-facing descriptions.

**Supported formats:** plain text files only (e.g. `.md`, `.txt`, `.json`, `.csv`). Binary formats (`.pdf`, `.docx`, etc.) are not supported. Any tool or resource that attempts to read or write a binary file must raise an error: `"'{filename}' is a binary format and is not supported. Use a plain text format such as .md or .txt."`

**Missing-file error.** Any tool or resource that operates on a non-existent document must raise an error with the exact message: `"Document '{filename}' does not exist."`

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
- Returns a JSON array of metadata objects, one per supported file. Resource `mimeType` must be `"application/json"`, and the array must be serialized to the content body via `json.dumps(...)` so the client's `json.loads` round-trip succeeds.
- Entries are sorted by `filename` ascending.
- **Binary files are skipped entirely** — they must not appear in the list. Filtering uses a non-raising predicate `is_binary(filename) -> bool` exposed by `core.doc_store` (sharing the `BINARY_EXTENSIONS` set with `check_binary`); do not call the raising helper for control flow.
- Each object has the following fields:
  - `filename` (str): e.g. `"notes.md"`.
  - `size_bytes` (int): file size in bytes.
  - `updated_at` (str): last-modified time as an ISO-8601 UTC timestamp with the literal `Z` suffix, formatted via `strftime("%Y-%m-%dT%H:%M:%SZ")` from `st_mtime` converted to UTC. Whole-second precision; sub-seconds are truncated.
  - `mime_type` (str): derived from the file extension (e.g. `"text/markdown"`, `"text/plain"`, `"application/json"`, `"text/csv"`). **Informational only** — intended for client-side UI use (icons, filtering). Document content is always served via `docs://{filename}` as `text/plain` regardless of this value.
- Example:

  ```json
  [
    {
      "filename": "notes.md",
      "size_bytes": 1432,
      "updated_at": "2026-05-01T14:08:02Z",
      "mime_type": "text/markdown"
    }
  ]
  ```

### `docs://{filename}`

- Return the content of `docs/{filename}` as plain text. Resource `mimeType` must be `"text/plain"` for all returned files, regardless of extension.
- Must raise the standard missing-file error if the file does not exist (see Document Store).
- Must raise the standard binary-format error if `filename` has a binary extension (see Document Store).
- **Purpose:** embedding document content directly into model context.

> Both `read_doc` (tool) and `docs://{filename}` (resource) return doc content. The distinction is intentional: the resource is for embedding content into model context; the tool is for programmatic access in agentic workflows.

## Prompts

All prompts are registered with an explicit `name` and `description` on `@mcp.prompt()`, and every argument uses `Field(description="...")` from Pydantic. Each prompt returns `list[base.Message]` (imported from `mcp.server.fastmcp.prompts`) — in practice a single-element list containing one `base.UserMessage`.

The registered `name` is kebab-case (the wire identifier the client sees) and is intentionally distinct from the snake_case Python function name.

**Filename handling.** Each prompt validates `filename` in two stages, using helpers exposed by `core.doc_store`:

1. **Binary rejection (raising).** Call `check_binary(filename)` first. If `filename` has a binary extension, this raises the standard binary-format error (see Document Store). Prompts must not suggest operating on binary files.
2. **Missing-file (non-raising).** Then check `exists(filename) -> bool`, a non-raising predicate. If the file is missing, return the helpful `base.UserMessage` shown in each prompt's bullets — do **not** raise the missing-file error. (This is why prompts use `exists` rather than the tools' raising `require_exists`: the missing-file outcome is a *prompt body*, not a server-side exception.)

**Prompt body.** The body does not read or embed the document's content directly. Instead it instructs the model to fetch the document via the `docs://{filename}` resource and, where applicable, to apply changes via the `edit_doc` tool. Routing reads through the resource means the binary-format guard is enforced a second time on the model side. The filename must appear inside `<filename>...</filename>` tags within the prompt body so it is unambiguous to the model.

### `rewrite-as-markdown`

```python
@mcp.prompt(
    name="rewrite-as-markdown",
    description="Rewrites the contents of a document in Markdown format.",
)
def rewrite_as_markdown(
    filename: str = Field(description="Filename of the document to rewrite."),
) -> list[base.Message]:
```

- If `filename` has a binary extension, raise the standard binary-format error (see Document Store) — via `check_binary(filename)`.
- Else if `docs/{filename}` does not exist (per `exists(filename)`), return `[base.UserMessage("The document '{filename}' does not exist. To create it, you could prompt: 'Create a new document called {filename} with the following content: ...'")]`.
- Otherwise return `[base.UserMessage(prompt)]` where `prompt` instructs the model to fetch the document via the `docs://{filename}` resource, reformat it with Markdown syntax — adding headers, bullet points, tables, and other structure as appropriate — and apply the rewrite via the `edit_doc` tool. The filename must appear inside `<filename>...</filename>` tags within the prompt body.

### `summarize-doc`

```python
@mcp.prompt(
    name="summarize-doc",
    description="Summarizes the contents of a document.",
)
def summarize_doc(
    filename: str = Field(description="Filename of the document to summarize."),
) -> list[base.Message]:
```

- If `filename` has a binary extension, raise the standard binary-format error (see Document Store) — via `check_binary(filename)`.
- Else if `docs/{filename}` does not exist (per `exists(filename)`), return `[base.UserMessage("The document '{filename}' does not exist. To create it, you could prompt: 'Create a new document called {filename} with the following content: ...'")]`.
- Otherwise return `[base.UserMessage(prompt)]` where `prompt` instructs the model to fetch the document via the `docs://{filename}` resource and produce a concise summary of its content. The filename must appear inside `<filename>...</filename>` tags within the prompt body.

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

- `result = await self.session().read_resource(AnyUrl(uri))`. The SDK's `read_resource` is typed to accept a pydantic `AnyUrl`, so wrap the incoming string before passing it through.
- Read the first item: `resource = result.contents[0]`. The server only ever returns a single content item for `docs://list` and `docs://{filename}`.
- Narrow on `isinstance(resource, types.TextResourceContents)`. The server never returns `BlobResourceContents` because it rejects binary filenames, so this is a defensive type guard rather than a real branch — the non-text path falls through and the method returns `None` implicitly.
- Inside the text branch: if `resource.mimeType == "application/json"`, return `json.loads(resource.text)`. Otherwise return `resource.text` unchanged.
- Add `import json` and `from pydantic import AnyUrl` to the module imports.

### Out of scope

- Retries, timeouts, logging, caching, and reconnection are explicitly excluded — the SDK and the existing `AsyncExitStack` lifecycle handle these.
