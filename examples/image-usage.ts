// Example: Using Claude Code SDK with image input
// Run: npx tsx examples/image-usage.ts

import { createClaudeClient } from "../src/index.js";
import { readFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));

// Sample 1x1 red PNG image (base64 encoded)
const SAMPLE_PNG_BASE64 =
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg==";

async function imageFromBase64() {
  console.log("=== Image from Base64 ===\n");

  const client = createClaudeClient();

  const message = await client.messages.create({
    model: "claude-sonnet-4-20250514",
    max_tokens: 256,
    messages: [
      {
        role: "user",
        content: [
          {
            type: "image",
            source: {
              type: "base64",
              media_type: "image/png",
              data: SAMPLE_PNG_BASE64,
            },
          },
          {
            type: "text",
            text: "What color is this image? Reply in one word.",
          },
        ],
      },
    ],
  });

  for (const block of message.content) {
    if (block.type === "text") {
      console.log("Response:", block.text);
    }
  }
}

async function imageFromFile() {
  console.log("\n=== Image from File ===\n");

  // Check if test image exists
  const testImagePath = join(__dirname, "test-image.png");
  let imageData: string;

  try {
    const buffer = readFileSync(testImagePath);
    imageData = buffer.toString("base64");
    console.log(`Loaded image from: ${testImagePath}`);
  } catch {
    console.log("No test image found, using sample image");
    imageData = SAMPLE_PNG_BASE64;
  }

  const client = createClaudeClient();

  const message = await client.messages.create({
    model: "claude-sonnet-4-20250514",
    max_tokens: 256,
    messages: [
      {
        role: "user",
        content: [
          {
            type: "image",
            source: {
              type: "base64",
              media_type: "image/png",
              data: imageData,
            },
          },
          {
            type: "text",
            text: "Describe this image briefly.",
          },
        ],
      },
    ],
  });

  for (const block of message.content) {
    if (block.type === "text") {
      console.log("Response:", block.text);
    }
  }
}

async function imageWithStreaming() {
  console.log("\n=== Image with Streaming ===\n");

  const client = createClaudeClient();

  const stream = client.messages.stream({
    model: "claude-sonnet-4-20250514",
    max_tokens: 256,
    messages: [
      {
        role: "user",
        content: [
          {
            type: "image",
            source: {
              type: "base64",
              media_type: "image/png",
              data: SAMPLE_PNG_BASE64,
            },
          },
          {
            type: "text",
            text: "What color is this image? Explain in a few words.",
          },
        ],
      },
    ],
  });

  process.stdout.write("Response: ");
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

async function main() {
  try {
    await imageFromBase64();
    await imageFromFile();
    await imageWithStreaming();
  } catch (error) {
    console.error("Error:", error);
    process.exit(1);
  }
}

main();
