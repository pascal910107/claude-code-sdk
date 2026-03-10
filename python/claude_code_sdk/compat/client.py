"""Anthropic SDK client factory for Claude Code CLI."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..types import PermissionMode

if TYPE_CHECKING:
    from anthropic import Anthropic, AsyncAnthropic


def create_claude_client(
    *,
    cwd: str | None = None,
    permission_mode: PermissionMode = "auto",
    binary_path: str = "claude",
    timeout_ms: int = 120_000,
) -> "Anthropic":
    """
    Creates an Anthropic SDK client that routes requests through Claude Code CLI.

    Args:
        cwd: Working directory for Claude Code CLI. Defaults to current directory.
        permission_mode: Permission mode for tool execution. Defaults to "auto".
        binary_path: Custom path to the claude executable. Defaults to "claude".
        timeout_ms: Timeout in milliseconds for CLI operations. Defaults to 120000.

    Returns:
        An Anthropic client configured to use Claude Code CLI.

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
    # Import here to make httpx and anthropic optional dependencies
    import httpx
    from anthropic import Anthropic

    from .http_client import CLITransport
    from .sessions import SessionStore

    sessions = SessionStore()
    transport = CLITransport(
        cwd=cwd,
        permission_mode=permission_mode,
        binary_path=binary_path,
        timeout_ms=timeout_ms,
        sessions=sessions,
    )

    http_client = httpx.Client(transport=transport)

    return Anthropic(
        api_key="not-needed-for-cli",  # CLI uses subscription, not API key
        http_client=http_client,
    )


def create_async_claude_client(
    *,
    cwd: str | None = None,
    permission_mode: PermissionMode = "auto",
    binary_path: str = "claude",
    timeout_ms: int = 120_000,
) -> "AsyncAnthropic":
    """
    Creates an async Anthropic SDK client that routes requests through Claude Code CLI.

    Args:
        cwd: Working directory for Claude Code CLI. Defaults to current directory.
        permission_mode: Permission mode for tool execution. Defaults to "auto".
        binary_path: Custom path to the claude executable. Defaults to "claude".
        timeout_ms: Timeout in milliseconds for CLI operations. Defaults to 120000.

    Returns:
        An async Anthropic client configured to use Claude Code CLI.

    Example:
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
    """
    # Import here to make httpx and anthropic optional dependencies
    import httpx
    from anthropic import AsyncAnthropic

    from .http_client import AsyncCLITransport
    from .sessions import SessionStore

    sessions = SessionStore()
    transport = AsyncCLITransport(
        cwd=cwd,
        permission_mode=permission_mode,
        binary_path=binary_path,
        timeout_ms=timeout_ms,
        sessions=sessions,
    )

    http_client = httpx.AsyncClient(transport=transport)

    return AsyncAnthropic(
        api_key="not-needed-for-cli",  # CLI uses subscription, not API key
        http_client=http_client,
    )
