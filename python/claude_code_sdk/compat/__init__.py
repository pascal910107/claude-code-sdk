"""Anthropic SDK compatibility layer for Claude Code CLI."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from anthropic import Anthropic, AsyncAnthropic

    from ..types import PermissionMode


def create_claude_client(
    *,
    cwd: str | None = None,
    permission_mode: "PermissionMode" = "auto",
    binary_path: str = "claude",
    timeout_ms: int = 120_000,
) -> "Anthropic":
    """Creates an Anthropic SDK client that routes requests through Claude Code CLI."""
    from .client import create_claude_client as _create

    return _create(
        cwd=cwd,
        permission_mode=permission_mode,
        binary_path=binary_path,
        timeout_ms=timeout_ms,
    )


def create_async_claude_client(
    *,
    cwd: str | None = None,
    permission_mode: "PermissionMode" = "auto",
    binary_path: str = "claude",
    timeout_ms: int = 120_000,
) -> "AsyncAnthropic":
    """Creates an async Anthropic SDK client that routes requests through Claude Code CLI."""
    from .client import create_async_claude_client as _create

    return _create(
        cwd=cwd,
        permission_mode=permission_mode,
        binary_path=binary_path,
        timeout_ms=timeout_ms,
    )


__all__ = ["create_claude_client", "create_async_claude_client"]
