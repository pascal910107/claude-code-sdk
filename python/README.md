# claude-code-sdk (Python)

Anthropic SDK compatibility layer for Claude Code CLI.

Use the familiar Anthropic SDK interface while leveraging your Claude Code subscription instead of API credits.

> **Note:** For the TypeScript/Node.js version, see the [root README](../README.md).

## Installation

```bash
# Clone the repository
git clone https://github.com/pascal910107/claude-code-sdk.git

# In your project, install with absolute path
cd /path/to/your-project
pip install -e /path/to/claude-code-sdk/python

# With Anthropic SDK (recommended)
pip install -e "/path/to/claude-code-sdk/python[anthropic]"
```

## Prerequisites

- Claude Code CLI installed and authenticated (`claude` command available)
- Python 3.10+

## Usage

### Basic Usage

```python
from claude_code_sdk import create_claude_client

client = create_claude_client()

message = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello, Claude!"}]
)

print(message.content[0].text)
```

### Streaming

```python
from claude_code_sdk import create_claude_client

client = create_claude_client()

with client.messages.stream(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Write a haiku about coding"}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

### Async Usage

```python
import asyncio
from claude_code_sdk import create_async_claude_client

async def main():
    client = create_async_claude_client()

    message = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": "Hello!"}]
    )
    print(message.content[0].text)

asyncio.run(main())
```

### Multi-turn Conversations

```python
from claude_code_sdk import create_claude_client

client = create_claude_client()
messages = []

# First turn
messages.append({"role": "user", "content": "My name is Alice."})
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=messages
)
messages.append({"role": "assistant", "content": response.content[0].text})

# Second turn - Claude remembers the context
messages.append({"role": "user", "content": "What's my name?"})
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=messages
)
print(response.content[0].text)  # "Your name is Alice."
```

## Configuration

```python
from claude_code_sdk import create_claude_client

client = create_claude_client(
    # Working directory for Claude Code CLI
    cwd="/path/to/project",

    # Permission mode: "auto", "acceptEdits", "plan", or "ask"
    permission_mode="auto",

    # Custom path to claude executable
    binary_path="/usr/local/bin/claude",

    # Timeout in milliseconds (default: 120000)
    timeout_ms=300000,
)
```

### Permission Modes

- `"auto"` - Automatically approve all tool executions (default, uses `--dangerously-skip-permissions`)
- `"acceptEdits"` - Auto-approve file edits, ask for other tools
- `"plan"` - Plan mode, more restrictive
- `"ask"` - Ask for permission on each tool use

## How It Works

This SDK creates an Anthropic client with a custom `httpx` transport that intercepts API requests and routes them through the Claude Code CLI instead. This allows you to:

1. Use your Claude Code subscription instead of API credits
2. Leverage Claude Code's tool execution capabilities
3. Maintain compatibility with existing Anthropic SDK code

## Supported Features

| Feature | Status |
|---------|--------|
| Text conversations | Supported |
| Streaming responses | Supported |
| Multi-turn conversations | Supported |
| System prompt | Supported |
| Async support | Supported |
| Images/PDF | Not supported (CLI limitation) |
| Custom tools | Not supported (CLI limitation) |

## License

MIT
