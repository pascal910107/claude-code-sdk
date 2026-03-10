"""
claude-code-sdk: Anthropic SDK compatibility layer for Claude Code CLI.

This package provides a drop-in replacement for the Anthropic SDK that routes
requests through the Claude Code CLI instead of the API.

Example:
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
"""

__version__ = "0.1.0"

from .compat import create_async_claude_client, create_claude_client
from .types import PermissionMode

__all__ = [
    "__version__",
    "create_claude_client",
    "create_async_claude_client",
    "PermissionMode",
]
