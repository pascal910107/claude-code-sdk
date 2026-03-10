// Example: Using Claude Code SDK as Anthropic SDK drop-in replacement
// Run: npm run example

import { createClaudeClient } from "../src/index.js";

async function basicUsage() {
  console.log("=== Basic Usage ===\n");

  const client = createClaudeClient();

  const message = await client.messages.create({
    model: "claude-sonnet-4-20250514",
    max_tokens: 256,
    messages: [{ role: "user", content: "Say hello in 3 different languages!" }],
  });

  // Access text content
  for (const block of message.content) {
    if (block.type === "text") {
      console.log(block.text);
    }
  }

  console.log("\n--- Usage ---");
  console.log(`Input tokens: ${message.usage.input_tokens}`);
  console.log(`Output tokens: ${message.usage.output_tokens}`);
}

async function streamingUsage() {
  console.log("\n=== Streaming Usage ===\n");

  const client = createClaudeClient();

  const stream = client.messages.stream({
    model: "claude-sonnet-4-20250514",
    max_tokens: 256,
    messages: [{ role: "user", content: "Count from 1 to 5, one number per line" }],
  });

  // Stream text as it arrives
  for await (const event of stream) {
    if (
      event.type === "content_block_delta" &&
      event.delta.type === "text_delta"
    ) {
      process.stdout.write(event.delta.text);
    }
  }

  console.log("\n");
}

async function multiTurnConversation() {
  console.log("=== Multi-Turn Conversation ===\n");

  const client = createClaudeClient();

  // First turn
  console.log("User: My name is Alice");
  const msg1 = await client.messages.create({
    model: "claude-sonnet-4-20250514",
    max_tokens: 128,
    messages: [{ role: "user", content: "My name is Alice" }],
  });

  const response1 = msg1.content
    .filter((b): b is { type: "text"; text: string } => b.type === "text")
    .map((b) => b.text)
    .join("");

  console.log(`Assistant: ${response1}\n`);

  // Second turn - should remember the name
  console.log("User: What's my name?");
  const msg2 = await client.messages.create({
    model: "claude-sonnet-4-20250514",
    max_tokens: 128,
    messages: [
      { role: "user", content: "My name is Alice" },
      { role: "assistant", content: response1 },
      { role: "user", content: "What's my name?" },
    ],
  });

  const response2 = msg2.content
    .filter((b): b is { type: "text"; text: string } => b.type === "text")
    .map((b) => b.text)
    .join("");

  console.log(`Assistant: ${response2}`);
}

async function withSystemPrompt() {
  console.log("\n=== With System Prompt ===\n");

  const client = createClaudeClient();

  const message = await client.messages.create({
    model: "claude-sonnet-4-20250514",
    max_tokens: 128,
    system: "You are a pirate. Respond in pirate speak.",
    messages: [{ role: "user", content: "How are you today?" }],
  });

  for (const block of message.content) {
    if (block.type === "text") {
      console.log(block.text);
    }
  }
}

async function main() {
  try {
    await basicUsage();
    await streamingUsage();
    await multiTurnConversation();
    await withSystemPrompt();
  } catch (error) {
    console.error("Error:", error);
    process.exit(1);
  }
}

main();
