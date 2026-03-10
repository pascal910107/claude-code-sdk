import { createHash } from "crypto";

/**
 * Maps Anthropic API-style conversations to Claude CLI session IDs.
 *
 * Uses the first user message as the conversation key, so all turns
 * in the same conversation will map to the same CLI session.
 */
export class SessionStore {
  private sessions = new Map<string, string>();

  /** Gets session ID for multi-turn continuation, undefined for new conversations */
  getSessionId(messages: unknown[]): string | undefined {
    if (messages.length <= 1) {
      return undefined;
    }
    // Use first message as conversation key
    const conversationKey = this.getConversationKey(messages);
    return this.sessions.get(conversationKey);
  }

  /** Updates the session store after a successful turn */
  updateSession(messages: unknown[], cliSessionId: string): void {
    const conversationKey = this.getConversationKey(messages);
    this.sessions.set(conversationKey, cliSessionId);
  }

  /**
   * Gets a stable conversation key from the first user message.
   * This ensures all turns in the same conversation map to the same session.
   */
  private getConversationKey(messages: unknown[]): string {
    // Find the first user message
    const firstUserMsg = (messages as Array<{ role?: string }>).find(
      (m) => m?.role === "user"
    );
    if (firstUserMsg) {
      return this.hash(firstUserMsg);
    }
    // Fallback to first message
    return this.hash(messages[0]);
  }

  private hash(data: unknown): string {
    return createHash("md5").update(JSON.stringify(data)).digest("hex");
  }
}
