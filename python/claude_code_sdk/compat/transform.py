"""Transform Anthropic API requests to CLI arguments."""

import json
import re
from typing import Any

from ..types import PermissionMode


def request_to_cli_args(
    body: dict[str, Any],
    session_id: str | None = None,
    *,
    permission_mode: PermissionMode = "auto",
) -> list[str]:
    """
    Transforms an Anthropic API request to Claude CLI arguments.

    Args:
        body: The Anthropic messages.create request body
        session_id: Optional session ID for multi-turn conversations
        permission_mode: Permission mode for CLI

    Returns:
        Array of CLI arguments
    """
    args: list[str] = [
        "--print",
        "--output-format",
        "stream-json",
        "--input-format",
        "stream-json",
        "--verbose",
    ]

    # Permission mode - default to auto for SDK usage
    if permission_mode == "auto":
        args.append("--dangerously-skip-permissions")
    elif permission_mode == "acceptEdits":
        args.extend(["--permission-mode", "acceptEdits"])
    elif permission_mode == "plan":
        args.extend(["--permission-mode", "plan"])
    # "ask" mode uses default behavior (no flag)

    # Model conversion
    model = parse_model(body.get("model", ""))
    if model != "sonnet":
        args.extend(["--model", model])

    # Session resume for multi-turn
    if session_id:
        args.extend(["--resume", session_id])

    # System prompt (if provided)
    system_prompt = body.get("system")
    if system_prompt:
        args.extend(["--system-prompt", system_prompt])

    # Note: prompt is now sent via stdin using stream-json format
    # This enables support for multimodal content (images)

    return args


def message_to_stream_json(message: dict[str, Any]) -> str:
    """
    Converts an Anthropic message to CLI stream-json input format.

    Args:
        message: The Anthropic message dict with 'role' and 'content'

    Returns:
        JSON string for stdin input
    """
    return json.dumps({
        "type": "user",
        "message": {
            "role": message.get("role"),
            "content": message.get("content"),
        },
    })


def parse_model(model: str) -> str:
    """Parses Anthropic model name to Claude CLI model format."""
    lower = model.lower()

    if "opus" in lower:
        return "opus"
    if "haiku" in lower:
        return "haiku"
    if "sonnet" in lower:
        return "sonnet"

    # For unknown models, try to extract the base name
    # e.g., "claude-3-5-sonnet-20240620" → "sonnet"
    match = re.search(r"claude[_-]?[\d.]*[_-]?[\d.]*[_-]?(opus|sonnet|haiku)", lower)
    if match:
        return match.group(1)

    # Default to sonnet for unknown models
    return "sonnet"
