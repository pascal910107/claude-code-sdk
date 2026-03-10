/** Permission modes for Claude Code CLI */
export type PermissionMode =
  | "auto" // --dangerously-skip-permissions
  | "acceptEdits" // --permission-mode acceptEdits
  | "plan" // --permission-mode plan
  | "ask"; // default, asks for each permission

// ─── Internal Event Types (used by parser) ───────────────────────────────────

export interface TextEvent {
  type: "text";
  content: string;
}

export interface ThinkingEvent {
  type: "thinking";
  content: string;
}

export interface ToolStartEvent {
  type: "tool_use";
  id: string;
  name: string;
  input?: Record<string, unknown>;
}

export interface ToolResultEvent {
  type: "tool_result";
  id: string;
  result: string;
}

export interface PermissionRequestEvent {
  type: "permission_request";
  tool: string;
  description: string;
  requestId: string;
}

export interface CompleteEvent {
  type: "complete";
  usage: {
    inputTokens: number;
    outputTokens: number;
  };
  costUsd?: number;
}

export interface ErrorEvent {
  type: "error";
  message: string;
}

export type ClaudeEvent =
  | TextEvent
  | ThinkingEvent
  | ToolStartEvent
  | ToolResultEvent
  | PermissionRequestEvent
  | CompleteEvent
  | ErrorEvent;

// ─── Internal Types for CLI JSON Parsing ─────────────────────────────────────

export interface RawSystemInit {
  type: "system";
  subtype: "init";
  session_id: string;
  tools?: string[];
  mcp_servers?: unknown[];
  model?: string;
  cwd?: string;
}

export interface RawAssistantMessage {
  type: "assistant";
  subtype: "message";
  message: {
    id: string;
    type: "message";
    role: "assistant";
    content: RawContentBlock[];
    model: string;
    stop_reason: string | null;
    stop_sequence: string | null;
    usage: {
      input_tokens: number;
      output_tokens: number;
      cache_creation_input_tokens?: number;
      cache_read_input_tokens?: number;
    };
  };
}

export type RawContentBlock =
  | { type: "text"; text: string }
  | { type: "thinking"; thinking: string }
  | { type: "tool_use"; id: string; name: string; input: Record<string, unknown> }
  | { type: "tool_result"; tool_use_id: string; content: string };

export interface RawContentBlockStart {
  type: "content_block_start";
  index: number;
  content_block: RawContentBlock;
}

export interface RawContentBlockDelta {
  type: "content_block_delta";
  index: number;
  delta:
    | { type: "text_delta"; text: string }
    | { type: "thinking_delta"; thinking: string }
    | { type: "input_json_delta"; partial_json: string };
}

export interface RawContentBlockStop {
  type: "content_block_stop";
  index: number;
}

export interface RawResultSuccess {
  type: "result";
  subtype: "success";
  result: string;
  is_error: boolean;
  duration_ms: number;
  duration_api_ms: number;
  num_turns: number;
  session_id: string;
  total_cost_usd?: number;
  usage?: {
    input_tokens: number;
    output_tokens: number;
    cache_creation_input_tokens?: number;
    cache_read_input_tokens?: number;
  };
}

export interface RawResultError {
  type: "result";
  subtype: "error";
  error: string;
  session_id?: string;
}

export type RawCliEvent =
  | RawSystemInit
  | RawAssistantMessage
  | RawContentBlockStart
  | RawContentBlockDelta
  | RawContentBlockStop
  | RawResultSuccess
  | RawResultError
  | { type: string; [key: string]: unknown };
