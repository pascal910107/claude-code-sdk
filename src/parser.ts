import type {
  ClaudeEvent,
  RawCliEvent,
  RawContentBlockDelta,
  RawContentBlockStart,
  RawResultError,
  RawResultSuccess,
  RawSystemInit,
} from "./types.js";

/**
 * State tracked during parsing
 */
export interface ParserState {
  sessionId: string | null;
  activeToolUses: Map<number, { id: string; name: string }>;
}

/**
 * Creates a new parser state
 */
export function createParserState(): ParserState {
  return {
    sessionId: null,
    activeToolUses: new Map(),
  };
}

/**
 * Parses a single line of stream-json output from Claude CLI
 * @param line Raw line from stdout
 * @param state Parser state (mutated)
 * @returns Array of ClaudeEvents to emit, or empty if line should be skipped
 */
export function parseLine(line: string, state: ParserState): ClaudeEvent[] {
  const trimmed = line.trim();
  if (!trimmed) return [];

  let raw: RawCliEvent;
  try {
    raw = JSON.parse(trimmed) as RawCliEvent;
  } catch {
    // Not JSON, ignore
    return [];
  }

  return parseRawEvent(raw, state);
}

/**
 * Parses a raw CLI event into ClaudeEvents
 */
function parseRawEvent(raw: RawCliEvent, state: ParserState): ClaudeEvent[] {
  const events: ClaudeEvent[] = [];

  switch (raw.type) {
    case "system": {
      if ((raw as RawSystemInit).subtype === "init") {
        const init = raw as RawSystemInit;
        state.sessionId = init.session_id;
        // system.init is internal, don't emit
      }
      break;
    }

    case "content_block_start": {
      const cbs = raw as RawContentBlockStart;
      const block = cbs.content_block;

      if (block.type === "tool_use") {
        state.activeToolUses.set(cbs.index, { id: block.id, name: block.name });
        events.push({
          type: "tool_use",
          id: block.id,
          name: block.name,
          input: block.input,
        });
      } else if (block.type === "text" && block.text) {
        events.push({ type: "text", content: block.text });
      } else if (block.type === "thinking" && block.thinking) {
        events.push({ type: "thinking", content: block.thinking });
      }
      break;
    }

    case "content_block_delta": {
      const cbd = raw as RawContentBlockDelta;
      const delta = cbd.delta;

      if (delta.type === "text_delta") {
        events.push({ type: "text", content: delta.text });
      } else if (delta.type === "thinking_delta") {
        events.push({ type: "thinking", content: delta.thinking });
      }
      // input_json_delta is for tool inputs, we can ignore incremental JSON
      break;
    }

    case "content_block_stop": {
      // If this was a tool use block, we could emit tool completion here
      // but we'll wait for the tool_result in the assistant message
      break;
    }

    case "assistant": {
      // Full assistant message - extract text and tool results
      const msg = raw as {
        message?: {
          content?: Array<{
            type: string;
            text?: string;
            thinking?: string;
            tool_use_id?: string;
            content?: string;
            id?: string;
            name?: string;
            input?: Record<string, unknown>;
          }>;
        };
      };
      if (msg.message?.content) {
        for (const block of msg.message.content) {
          switch (block.type) {
            case "text":
              if (block.text) {
                events.push({ type: "text", content: block.text });
              }
              break;
            case "thinking":
              if (block.thinking) {
                events.push({ type: "thinking", content: block.thinking });
              }
              break;
            case "tool_use":
              if (block.id && block.name) {
                events.push({
                  type: "tool_use",
                  id: block.id,
                  name: block.name,
                  input: block.input,
                });
              }
              break;
            case "tool_result":
              if (block.tool_use_id) {
                events.push({
                  type: "tool_result",
                  id: block.tool_use_id,
                  result: typeof block.content === "string" ? block.content : JSON.stringify(block.content),
                });
              }
              break;
          }
        }
      }
      break;
    }

    case "result": {
      if ((raw as RawResultSuccess).subtype === "success") {
        const success = raw as RawResultSuccess;
        state.sessionId = success.session_id;
        const completeEvent: ClaudeEvent = {
          type: "complete",
          usage: {
            inputTokens: success.usage?.input_tokens ?? 0,
            outputTokens: success.usage?.output_tokens ?? 0,
          },
        };
        if (success.total_cost_usd !== undefined) {
          (completeEvent as { costUsd: number }).costUsd = success.total_cost_usd;
        }
        events.push(completeEvent);
      } else if ((raw as RawResultError).subtype === "error") {
        const error = raw as RawResultError;
        events.push({ type: "error", message: error.error });
      }
      break;
    }

    default:
      // Unknown event type, ignore
      break;
  }

  return events;
}

/**
 * Creates a line-based async iterator from a readable stream
 */
export async function* streamLines(
  stream: NodeJS.ReadableStream
): AsyncGenerator<string, void, undefined> {
  let buffer = "";

  for await (const chunk of stream) {
    buffer += chunk.toString();
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      yield line;
    }
  }

  // Emit remaining buffer if any
  if (buffer.trim()) {
    yield buffer;
  }
}
