import { spawn, type ChildProcess } from "child_process";
import { requestToCliArgs, type MessagesRequest } from "./transform.js";
import { SessionStore } from "./sessions.js";
import { streamLines, parseLine, createParserState } from "../parser.js";
import type { PermissionMode } from "../types.js";

/** Default timeout in milliseconds (2 minutes) */
const DEFAULT_TIMEOUT_MS = 120_000;

export interface CreateCustomFetchOptions {
  cwd?: string | undefined;
  permissionMode?: PermissionMode | undefined;
  binaryPath?: string | undefined;
  /** Timeout in milliseconds. Default: 120000 (2 minutes) */
  timeoutMs?: number | undefined;
}

/** Creates a custom fetch that intercepts Anthropic API calls and routes them through CLI */
export function createCustomFetch(
  options: CreateCustomFetchOptions,
  sessions: SessionStore
): typeof fetch {
  const cwd = options.cwd ?? process.cwd();
  const binaryPath = options.binaryPath ?? "claude";
  const timeoutMs = options.timeoutMs ?? DEFAULT_TIMEOUT_MS;

  return async (
    input: RequestInfo | URL,
    init?: RequestInit
  ): Promise<Response> => {
    const url = typeof input === "string" ? input : input.toString();

    // Only intercept /v1/messages endpoint
    if (url.endsWith("/v1/messages")) {
      return handleMessagesRequest(init, {
        cwd,
        binaryPath,
        permissionMode: options.permissionMode,
        timeoutMs,
        sessions,
      });
    }

    // Other endpoints - pass through to real fetch
    // This shouldn't happen in normal usage, but provides fallback
    return fetch(input, init);
  };
}

interface HandleRequestOptions {
  cwd: string;
  binaryPath: string;
  permissionMode?: PermissionMode | undefined;
  timeoutMs: number;
  sessions: SessionStore;
}

/** Helper to create a timeout promise that rejects after specified ms */
function createTimeout(ms: number, child: ChildProcess): Promise<never> {
  return new Promise((_, reject) => {
    const timer = setTimeout(() => {
      child.kill("SIGTERM");
      reject(new Error(`CLI timeout after ${ms}ms`));
    }, ms);

    // Clean up timer if process exits normally
    child.on("close", () => clearTimeout(timer));
  });
}

/** Collect stderr output for error messages */
async function collectStderr(child: ChildProcess): Promise<string> {
  const chunks: Buffer[] = [];
  if (child.stderr) {
    for await (const chunk of child.stderr) {
      chunks.push(Buffer.from(chunk));
    }
  }
  return Buffer.concat(chunks).toString("utf-8").trim();
}

async function handleMessagesRequest(
  init: RequestInit | undefined,
  options: HandleRequestOptions
): Promise<Response> {
  const body = JSON.parse(init?.body as string) as MessagesRequest;
  const isStreaming = body.stream === true;

  // Get session ID for multi-turn conversations
  const sessionId = options.sessions.getSessionId(body.messages);

  // Build CLI arguments
  const cliArgs = requestToCliArgs(body, sessionId, {
    permissionMode: options.permissionMode,
  });

  if (isStreaming) {
    return createStreamingResponse(cliArgs, options, body);
  } else {
    return createNonStreamingResponse(cliArgs, options, body);
  }
}

async function createStreamingResponse(
  cliArgs: string[],
  options: HandleRequestOptions,
  requestBody: MessagesRequest
): Promise<Response> {
  const child = spawn(options.binaryPath, cliArgs, {
    cwd: options.cwd,
    stdio: ["pipe", "pipe", "pipe"],
    env: {
      ...process.env,
      NO_COLOR: "1",
    },
  });

  // Close stdin immediately - CLI doesn't need input
  child.stdin?.end();

  const parserState = createParserState();
  const messageId = `msg_${Date.now()}`;
  let outputTokens = 0;

  // Set up timeout
  const timeoutPromise = createTimeout(options.timeoutMs, child);

  // Create a readable stream for SSE
  const stream = new ReadableStream<Uint8Array>({
    async start(controller) {
      const encoder = new TextEncoder();

      // Helper to send SSE event
      const sendEvent = (eventType: string, data: unknown) => {
        const json = JSON.stringify(data);
        controller.enqueue(encoder.encode(`event: ${eventType}\ndata: ${json}\n\n`));
      };

      // Send initial message_start event
      sendEvent("message_start", {
        type: "message_start",
        message: {
          id: messageId,
          type: "message",
          role: "assistant",
          content: [],
          model: requestBody.model,
          stop_reason: null,
          stop_sequence: null,
          usage: { input_tokens: 0, output_tokens: 0 },
        },
      });

      let contentBlockIndex = 0;
      let currentBlockType: "text" | "thinking" | "tool_use" | null = null;

      // Race between processing and timeout
      const processStream = async () => {
        for await (const line of streamLines(child.stdout)) {
          const events = parseLine(line, parserState);

          // Update session ID from parser state
          if (parserState.sessionId) {
            options.sessions.updateSession(requestBody.messages, parserState.sessionId);
          }

          for (const event of events) {
            switch (event.type) {
              case "text": {
                // Start new text block if needed
                if (currentBlockType !== "text") {
                  if (currentBlockType !== null) {
                    sendEvent("content_block_stop", {
                      type: "content_block_stop",
                      index: contentBlockIndex - 1,
                    });
                  }
                  sendEvent("content_block_start", {
                    type: "content_block_start",
                    index: contentBlockIndex,
                    content_block: { type: "text", text: "" },
                  });
                  currentBlockType = "text";
                }

                sendEvent("content_block_delta", {
                  type: "content_block_delta",
                  index: contentBlockIndex,
                  delta: { type: "text_delta", text: event.content },
                });
                break;
              }

              case "thinking": {
                // Handle thinking blocks (extended thinking)
                if (currentBlockType !== "thinking") {
                  if (currentBlockType !== null) {
                    sendEvent("content_block_stop", {
                      type: "content_block_stop",
                      index: contentBlockIndex - 1,
                    });
                  }
                  contentBlockIndex++;
                  sendEvent("content_block_start", {
                    type: "content_block_start",
                    index: contentBlockIndex,
                    content_block: { type: "thinking", thinking: "" },
                  });
                  currentBlockType = "thinking";
                }

                sendEvent("content_block_delta", {
                  type: "content_block_delta",
                  index: contentBlockIndex,
                  delta: { type: "thinking_delta", thinking: event.content },
                });
                break;
              }

              case "tool_use": {
                // Close previous block
                if (currentBlockType !== null) {
                  sendEvent("content_block_stop", {
                    type: "content_block_stop",
                    index: contentBlockIndex,
                  });
                  contentBlockIndex++;
                }

                sendEvent("content_block_start", {
                  type: "content_block_start",
                  index: contentBlockIndex,
                  content_block: {
                    type: "tool_use",
                    id: event.id,
                    name: event.name,
                    input: event.input ?? {},
                  },
                });
                currentBlockType = "tool_use";
                break;
              }

              case "complete": {
                outputTokens = event.usage.outputTokens;
                break;
              }

              case "error": {
                sendEvent("error", {
                  type: "error",
                  error: { type: "api_error", message: event.message },
                });
                break;
              }
            }
          }
        }

        // Close final content block
        if (currentBlockType !== null) {
          sendEvent("content_block_stop", {
            type: "content_block_stop",
            index: contentBlockIndex,
          });
        }

        // Send message_delta and message_stop
        sendEvent("message_delta", {
          type: "message_delta",
          delta: { stop_reason: "end_turn", stop_sequence: null },
          usage: { output_tokens: outputTokens },
        });

        sendEvent("message_stop", { type: "message_stop" });
      };

      try {
        // Race between processing and timeout
        await Promise.race([processStream(), timeoutPromise]);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : String(err);
        sendEvent("error", {
          type: "error",
          error: { type: "api_error", message: errorMessage },
        });
      } finally {
        controller.close();
      }
    },
  });

  return new Response(stream, {
    status: 200,
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  });
}

async function createNonStreamingResponse(
  cliArgs: string[],
  options: HandleRequestOptions,
  requestBody: MessagesRequest
): Promise<Response> {
  const child = spawn(options.binaryPath, cliArgs, {
    cwd: options.cwd,
    stdio: ["pipe", "pipe", "pipe"],
    env: {
      ...process.env,
      NO_COLOR: "1",
    },
  });

  // Close stdin immediately - CLI doesn't need input
  child.stdin?.end();

  const parserState = createParserState();
  const contentBlocks: Array<{ type: string; text?: string; thinking?: string; id?: string; name?: string; input?: unknown }> = [];
  let currentText = "";
  let inputTokens = 0;
  let outputTokens = 0;
  let errorMessage: string | null = null;

  // Set up timeout
  const timeoutPromise = createTimeout(options.timeoutMs, child);

  // Collect stderr in background for error reporting
  const stderrPromise = collectStderr(child);

  // Process all events
  const processStream = async () => {
    for await (const line of streamLines(child.stdout)) {
      const events = parseLine(line, parserState);

      if (parserState.sessionId) {
        options.sessions.updateSession(requestBody.messages, parserState.sessionId);
      }

      for (const event of events) {
        switch (event.type) {
          case "text":
            currentText += event.content;
            break;
          case "tool_use":
            // Flush accumulated text before tool
            if (currentText) {
              contentBlocks.push({ type: "text", text: currentText });
              currentText = "";
            }
            contentBlocks.push({
              type: "tool_use",
              id: event.id,
              name: event.name,
              input: event.input ?? {},
            });
            break;
          case "complete":
            inputTokens = event.usage.inputTokens;
            outputTokens = event.usage.outputTokens;
            break;
          case "error":
            errorMessage = event.message;
            break;
        }
      }
    }

    // Flush remaining text
    if (currentText) {
      contentBlocks.push({ type: "text", text: currentText });
    }
  };

  try {
    // Race between processing and timeout
    await Promise.race([processStream(), timeoutPromise]);
  } catch (err) {
    // On timeout or other errors, include stderr in error message
    const stderr = await stderrPromise;
    const errMsg = err instanceof Error ? err.message : String(err);
    const fullError = stderr ? `${errMsg}\nstderr: ${stderr}` : errMsg;

    return new Response(
      JSON.stringify({
        type: "error",
        error: { type: "api_error", message: fullError },
      }),
      {
        status: 408,
        headers: { "Content-Type": "application/json" },
      }
    );
  }

  // Wait for process to exit
  await new Promise<void>((resolve) => {
    child.on("close", () => resolve());
  });

  if (errorMessage) {
    return new Response(
      JSON.stringify({
        type: "error",
        error: { type: "api_error", message: errorMessage },
      }),
      {
        status: 400,
        headers: { "Content-Type": "application/json" },
      }
    );
  }

  const response = {
    id: `msg_${Date.now()}`,
    type: "message",
    role: "assistant",
    content: contentBlocks,
    model: requestBody.model,
    stop_reason: "end_turn",
    stop_sequence: null,
    usage: {
      input_tokens: inputTokens,
      output_tokens: outputTokens,
    },
  };

  return new Response(JSON.stringify(response), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}
