import Anthropic from "@anthropic-ai/sdk";
import { createCustomFetch } from "./http-client.js";
import { SessionStore } from "./sessions.js";
import type { PermissionMode } from "../types.js";

/**
 * Options for creating a Claude client that uses CLI
 */
export interface CreateClaudeClientOptions {
  /**
   * Working directory for Claude Code CLI
   * @default process.cwd()
   */
  cwd?: string;

  /**
   * Permission mode for tool execution
   * @default "auto" (skips permission prompts)
   */
  permissionMode?: PermissionMode;

  /**
   * Custom path to the claude executable
   * @default "claude"
   */
  binaryPath?: string;

  /**
   * Timeout in milliseconds for CLI operations
   * @default 120000 (2 minutes)
   */
  timeoutMs?: number;
}

/** Creates an Anthropic SDK client that routes requests through Claude Code CLI */
export function createClaudeClient(options: CreateClaudeClientOptions = {}): Anthropic {
  const sessions = new SessionStore();
  const customFetch = createCustomFetch(
    {
      cwd: options.cwd,
      permissionMode: options.permissionMode,
      binaryPath: options.binaryPath,
      timeoutMs: options.timeoutMs,
    },
    sessions
  );

  return new Anthropic({
    apiKey: "not-needed-for-cli", // CLI uses subscription, not API key
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    fetch: customFetch as any,
  });
}
