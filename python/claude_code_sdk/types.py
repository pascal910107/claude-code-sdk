"""Type definitions for claude-code-sdk."""

from dataclasses import dataclass
from typing import Any, Literal, Optional, TypedDict

# Permission modes for Claude Code CLI
PermissionMode = Literal["auto", "acceptEdits", "plan", "ask"]


# ─── Event Types ────────────────────────────────────────────────────────────


@dataclass
class TextEvent:
    """Text content from assistant."""

    type: Literal["text"] = "text"
    content: str = ""


@dataclass
class ThinkingEvent:
    """Thinking/reasoning content (extended thinking)."""

    type: Literal["thinking"] = "thinking"
    content: str = ""


@dataclass
class ToolUseEvent:
    """Tool invocation by assistant."""

    type: Literal["tool_use"] = "tool_use"
    id: str = ""
    name: str = ""
    input: Optional[dict[str, Any]] = None


@dataclass
class ToolResultEvent:
    """Result from tool execution."""

    type: Literal["tool_result"] = "tool_result"
    id: str = ""
    result: str = ""


@dataclass
class PermissionRequestEvent:
    """Permission request for tool execution."""

    type: Literal["permission_request"] = "permission_request"
    tool: str = ""
    description: str = ""
    request_id: str = ""


@dataclass
class CompleteEvent:
    """Completion event with usage stats."""

    type: Literal["complete"] = "complete"
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: Optional[float] = None


@dataclass
class ErrorEvent:
    """Error event."""

    type: Literal["error"] = "error"
    message: str = ""


ClaudeEvent = (
    TextEvent
    | ThinkingEvent
    | ToolUseEvent
    | ToolResultEvent
    | PermissionRequestEvent
    | CompleteEvent
    | ErrorEvent
)


# ─── Raw CLI Event Types (TypedDict for JSON parsing) ───────────────────────


class RawUsage(TypedDict, total=False):
    """Raw usage stats from CLI."""

    input_tokens: int
    output_tokens: int
    cache_creation_input_tokens: int
    cache_read_input_tokens: int


class RawSystemInit(TypedDict, total=False):
    """System init event from CLI."""

    type: Literal["system"]
    subtype: Literal["init"]
    session_id: str
    tools: list[str]
    mcp_servers: list[Any]
    model: str
    cwd: str


class RawTextBlock(TypedDict):
    """Text content block."""

    type: Literal["text"]
    text: str


class RawThinkingBlock(TypedDict):
    """Thinking content block."""

    type: Literal["thinking"]
    thinking: str


class RawToolUseBlock(TypedDict):
    """Tool use content block."""

    type: Literal["tool_use"]
    id: str
    name: str
    input: dict[str, Any]


class RawToolResultBlock(TypedDict):
    """Tool result content block."""

    type: Literal["tool_result"]
    tool_use_id: str
    content: str


RawContentBlock = RawTextBlock | RawThinkingBlock | RawToolUseBlock | RawToolResultBlock


class RawMessage(TypedDict, total=False):
    """Raw assistant message."""

    id: str
    type: Literal["message"]
    role: Literal["assistant"]
    content: list[RawContentBlock]
    model: str
    stop_reason: str | None
    stop_sequence: str | None
    usage: RawUsage


class RawAssistantMessage(TypedDict):
    """Assistant message event from CLI."""

    type: Literal["assistant"]
    subtype: Literal["message"]
    message: RawMessage


class RawContentBlockStart(TypedDict):
    """Content block start event."""

    type: Literal["content_block_start"]
    index: int
    content_block: RawContentBlock


class RawTextDelta(TypedDict):
    """Text delta."""

    type: Literal["text_delta"]
    text: str


class RawThinkingDelta(TypedDict):
    """Thinking delta."""

    type: Literal["thinking_delta"]
    thinking: str


class RawInputJsonDelta(TypedDict):
    """Input JSON delta for tool use."""

    type: Literal["input_json_delta"]
    partial_json: str


RawDelta = RawTextDelta | RawThinkingDelta | RawInputJsonDelta


class RawContentBlockDelta(TypedDict):
    """Content block delta event."""

    type: Literal["content_block_delta"]
    index: int
    delta: RawDelta


class RawContentBlockStop(TypedDict):
    """Content block stop event."""

    type: Literal["content_block_stop"]
    index: int


class RawResultSuccess(TypedDict, total=False):
    """Successful result event from CLI."""

    type: Literal["result"]
    subtype: Literal["success"]
    result: str
    is_error: bool
    duration_ms: int
    duration_api_ms: int
    num_turns: int
    session_id: str
    total_cost_usd: float
    usage: RawUsage


class RawResultError(TypedDict, total=False):
    """Error result event from CLI."""

    type: Literal["result"]
    subtype: Literal["error"]
    error: str
    session_id: str


RawCliEvent = (
    RawSystemInit
    | RawAssistantMessage
    | RawContentBlockStart
    | RawContentBlockDelta
    | RawContentBlockStop
    | RawResultSuccess
    | RawResultError
    | dict[str, Any]  # Unknown event types
)
