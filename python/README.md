# claude-code-sdk (Python)

Anthropic SDK compatibility layer for Claude Code CLI.

> **Note:** For TypeScript/Node.js, see the [root README](../README.md).

## Prerequisites

- Claude Code CLI installed and authenticated (`claude` command available)
- Python 3.10+

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

## Quick Start

```python
from claude_code_sdk import create_claude_client

client = create_claude_client()

message = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello!"}]
)

print(message.content[0].text)
```

## Async Usage

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

## Configuration

```python
client = create_claude_client(
    cwd="/path/to/project",       # Working directory
    permission_mode="auto",        # "auto" | "acceptEdits" | "plan" | "ask"
    binary_path="claude",          # CLI path
    timeout_ms=120000,             # Timeout in milliseconds (default: 2 minutes)
)
```

| Permission Mode | Behavior |
|-----------------|----------|
| `auto` (default) | Skips all permission prompts |
| `acceptEdits` | Auto-accepts file edits |
| `plan` | Planning only, no execution |
| `ask` | Requires confirmation for each operation |

## Supported Features

| Feature | Status |
|---------|--------|
| Text messages | ✓ |
| Streaming | ✓ |
| Multi-turn conversations | ✓ |
| System prompt | ✓ |
| Async support | ✓ |
| Images (base64) | ✓ |
| PDF (base64) | ✓ |
| Custom tools | ✗ |

## Examples

See [`examples/`](./examples/) for complete examples:

- [`basic_usage.py`](./examples/basic_usage.py) — Text, streaming, multi-turn, async
- [`multimodal_usage.py`](./examples/multimodal_usage.py) — Image and PDF input

```bash
python examples/basic_usage.py
python examples/multimodal_usage.py
```

## License

MIT
