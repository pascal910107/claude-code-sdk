import type { PermissionMode } from "../types.js";

/**
 * Anthropic API message format
 */
export interface AnthropicMessage {
  role: "user" | "assistant";
  content: string | AnthropicContentBlock[];
}

export type AnthropicContentBlock =
  | { type: "text"; text: string }
  | { type: "image"; source: { type: "base64"; media_type: string; data: string } }
  | { type: "tool_use"; id: string; name: string; input: Record<string, unknown> }
  | { type: "tool_result"; tool_use_id: string; content: string };

/**
 * Anthropic messages.create request body
 */
export interface MessagesRequest {
  model: string;
  max_tokens: number;
  messages: AnthropicMessage[];
  system?: string;
  temperature?: number;
  top_p?: number;
  top_k?: number;
  stream?: boolean;
  stop_sequences?: string[];
  tools?: unknown[];
  tool_choice?: unknown;
  metadata?: { user_id?: string };
}

/**
 * Options for CLI argument transformation
 */
export interface TransformOptions {
  permissionMode?: PermissionMode | undefined;
}

/**
 * Transforms an Anthropic API request to Claude CLI arguments
 *
 * @param body The Anthropic messages.create request body
 * @param sessionId Optional session ID for multi-turn conversations
 * @param options Additional transformation options
 * @returns Array of CLI arguments
 */
export function requestToCliArgs(
  body: MessagesRequest,
  sessionId?: string,
  options: TransformOptions = {}
): string[] {
  const args: string[] = [
    "--print",
    "--output-format",
    "stream-json",
    "--input-format",
    "stream-json",
    "--verbose",
  ];

  // Permission mode - default to auto for SDK usage
  const permissionMode = options.permissionMode ?? "auto";
  switch (permissionMode) {
    case "auto":
      args.push("--dangerously-skip-permissions");
      break;
    case "acceptEdits":
      args.push("--permission-mode", "acceptEdits");
      break;
    case "plan":
      args.push("--permission-mode", "plan");
      break;
    // "ask" mode uses default behavior (no flag)
  }

  // Model conversion
  const model = parseModel(body.model);
  if (model !== "sonnet") {
    args.push("--model", model);
  }

  // Session resume for multi-turn
  if (sessionId) {
    args.push("--resume", sessionId);
  }

  // System prompt (if provided)
  if (body.system) {
    args.push("--system-prompt", body.system);
  }

  // Note: prompt is now sent via stdin using stream-json format
  // This enables support for multimodal content (images)

  return args;
}

/**
 * Converts an Anthropic message to CLI stream-json input format
 *
 * @param message The Anthropic message to convert
 * @returns JSON string for stdin input
 */
export function messageToStreamJson(message: AnthropicMessage): string {
  return JSON.stringify({
    type: "user",
    message: {
      role: message.role,
      content: message.content,
    },
  });
}

/**
 * Parses Anthropic model name to Claude CLI model format
 */
function parseModel(model: string): string {
  const lower = model.toLowerCase();

  if (lower.includes("opus")) return "opus";
  if (lower.includes("haiku")) return "haiku";
  if (lower.includes("sonnet")) return "sonnet";

  // For unknown models, try to extract the base name
  // e.g., "claude-3-5-sonnet-20240620" → "sonnet"
  const match = lower.match(/claude[_-]?[\d.]*[_-]?[\d.]*[_-]?(opus|sonnet|haiku)/);
  if (match?.[1]) {
    return match[1];
  }

  // Default to sonnet for unknown models
  return "sonnet";
}
