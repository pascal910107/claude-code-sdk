"""Transform Anthropic API requests to CLI arguments."""

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

    # Extract the prompt (last user message)
    messages = body.get("messages", [])
    prompt = extract_prompt(messages)
    args.append(prompt)

    return args


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


def extract_prompt(messages: list[dict[str, Any]]) -> str:
    """Extracts the text prompt from the last user message."""
    # Find the last user message
    for i in range(len(messages) - 1, -1, -1):
        msg = messages[i]
        if msg.get("role") == "user":
            return extract_text_content(msg.get("content"))

    # Fallback: extract from any message with text
    for i in range(len(messages) - 1, -1, -1):
        msg = messages[i]
        text = extract_text_content(msg.get("content"))
        if text:
            return text

    return ""


def extract_text_content(content: str | list[dict[str, Any]] | None) -> str:
    """Extracts text content from a message content field."""
    if not content:
        return ""

    if isinstance(content, str):
        return content

    # Array of content blocks
    texts = []
    for block in content:
        if isinstance(block, dict) and block.get("type") == "text":
            texts.append(block.get("text", ""))

    return "\n".join(texts)
