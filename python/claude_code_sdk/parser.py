"""CLI JSON output parser for claude-code-sdk."""

import json
from dataclasses import dataclass, field
from typing import Any

from .types import (
    ClaudeEvent,
    CompleteEvent,
    ErrorEvent,
    TextEvent,
    ThinkingEvent,
    ToolResultEvent,
    ToolUseEvent,
)


@dataclass
class ParserState:
    """State tracked during parsing."""

    session_id: str | None = None
    active_tool_uses: dict[int, dict[str, str]] = field(default_factory=dict)


def create_parser_state() -> ParserState:
    """Creates a new parser state."""
    return ParserState()


def parse_line(line: str, state: ParserState) -> list[ClaudeEvent]:
    """
    Parses a single line of stream-json output from Claude CLI.

    Args:
        line: Raw line from stdout
        state: Parser state (mutated)

    Returns:
        List of ClaudeEvents to emit, or empty if line should be skipped
    """
    trimmed = line.strip()
    if not trimmed:
        return []

    try:
        raw = json.loads(trimmed)
    except json.JSONDecodeError:
        # Not JSON, ignore
        return []

    return parse_raw_event(raw, state)


def parse_raw_event(raw: dict[str, Any], state: ParserState) -> list[ClaudeEvent]:
    """Parses a raw CLI event into ClaudeEvents."""
    events: list[ClaudeEvent] = []
    event_type = raw.get("type")

    if event_type == "system":
        if raw.get("subtype") == "init":
            state.session_id = raw.get("session_id")
            # system.init is internal, don't emit

    elif event_type == "content_block_start":
        block = raw.get("content_block", {})
        index = raw.get("index", 0)

        if block.get("type") == "tool_use":
            state.active_tool_uses[index] = {
                "id": block.get("id", ""),
                "name": block.get("name", ""),
            }
            events.append(
                ToolUseEvent(
                    id=block.get("id", ""),
                    name=block.get("name", ""),
                    input=block.get("input"),
                )
            )
        elif block.get("type") == "text" and block.get("text"):
            events.append(TextEvent(content=block.get("text", "")))
        elif block.get("type") == "thinking" and block.get("thinking"):
            events.append(ThinkingEvent(content=block.get("thinking", "")))

    elif event_type == "content_block_delta":
        delta = raw.get("delta", {})

        if delta.get("type") == "text_delta":
            events.append(TextEvent(content=delta.get("text", "")))
        elif delta.get("type") == "thinking_delta":
            events.append(ThinkingEvent(content=delta.get("thinking", "")))
        # input_json_delta is for tool inputs, we can ignore incremental JSON

    elif event_type == "content_block_stop":
        # If this was a tool use block, we could emit tool completion here
        # but we'll wait for the tool_result in the assistant message
        pass

    elif event_type == "assistant":
        # Full assistant message - extract text and tool results
        message = raw.get("message", {})
        content = message.get("content", [])

        for block in content:
            block_type = block.get("type")

            if block_type == "text":
                text = block.get("text")
                if text:
                    events.append(TextEvent(content=text))

            elif block_type == "thinking":
                thinking = block.get("thinking")
                if thinking:
                    events.append(ThinkingEvent(content=thinking))

            elif block_type == "tool_use":
                tool_id = block.get("id")
                name = block.get("name")
                if tool_id and name:
                    events.append(
                        ToolUseEvent(
                            id=tool_id,
                            name=name,
                            input=block.get("input"),
                        )
                    )

            elif block_type == "tool_result":
                tool_use_id = block.get("tool_use_id")
                if tool_use_id:
                    content_val = block.get("content", "")
                    if not isinstance(content_val, str):
                        content_val = json.dumps(content_val)
                    events.append(
                        ToolResultEvent(
                            id=tool_use_id,
                            result=content_val,
                        )
                    )

    elif event_type == "result":
        if raw.get("subtype") == "success":
            state.session_id = raw.get("session_id")
            usage = raw.get("usage", {})
            events.append(
                CompleteEvent(
                    input_tokens=usage.get("input_tokens", 0),
                    output_tokens=usage.get("output_tokens", 0),
                    cost_usd=raw.get("total_cost_usd"),
                )
            )
        elif raw.get("subtype") == "error":
            events.append(ErrorEvent(message=raw.get("error", "Unknown error")))

    return events
