# Claude MCP Shell

An MCP server and CLI chat interface for Claude, implementing tools, resources, and prompts through a document store.

## Features

- Interactive CLI chat with Claude (powered by the Anthropic API)
- Document management via MCP tools (`read_doc`, `create_doc`, `edit_doc`, `delete_doc`)
- Document resources (`docs://list`, `docs://{filename}`)
- Slash command prompts (`/summarize`, `/rewrite-as-markdown`)
- `@filename` syntax to include document content in queries
- Tab completion for commands

## Prerequisites

- Python 3.10+
- Anthropic API Key

## Setup

### Step 1: Configure the environment variables

Create or edit the `.env` file in the project root:

```
ANTHROPIC_API_KEY=""  # Enter your Anthropic API secret key
CLAUDE_MODEL=""       # e.g. claude-sonnet-4-5
```

### Step 2: Install dependencies

#### Option 1: Setup with uv (Recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package installer and resolver.

1. Install uv, if not already installed:

```bash
pip install uv
```

2. Create and activate a virtual environment:

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:

```bash
uv pip install -e .
```

4. Run the project:

```bash
uv run main.py
```

#### Option 2: Setup without uv

1. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -e .
```

3. Run the project:

```bash
python main.py
```

## Usage

### Basic Interaction

Type your message and press Enter to chat with Claude. Press `Ctrl+C` to exit.

```
> What is the capital of France?
```

### Document Retrieval

Use the `@` symbol followed by a document filename to include document content in your query:

```
> Tell me about @project-setup.md
```

### Commands

Use the `/` prefix to execute commands defined in the MCP server:

```
> /summarize project-setup.md
```

Commands will auto-complete when you press Tab.

## Document Store

Documents are stored as individual files in a `docs/` directory at the project root. All MCP tools and resources read from and write to this directory directly — there is no in-memory store.

## Development

### Linting and Typing Check

There are no lint or type checks implemented.
