/**
 * Multimodal Usage Examples - Images and PDFs
 *
 * This example demonstrates how to send images and PDF documents to Claude
 * using the same API format as the official Anthropic SDK.
 *
 * Run: npx tsx examples/multimodal-usage.ts
 */

import { createClaudeClient } from "../src/index.js";
import { readFileSync, existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));

// =============================================================================
// Test Data
// =============================================================================

// Sample 100x100 red PNG image (base64 encoded)
// In real usage, you would load this from a file or receive it from an API
const SAMPLE_PNG_BASE64 =
  "iVBORw0KGgoAAAANSUhEUgAAAGQAAABkCAIAAAD/gAIDAAAAkElEQVR42u3QMQ0AAAjAsPk3DRb4eJpUQZviSIEsWbJkyUKBLFmyZMlCgSxZsmTJQoEsWbJkyUKBLFmyZMlCgSxZsmTJQoEsWbJkyUKBLFmyZMlCgSxZsmTJQoEsWbJkyUKBLFmyZMlCgSxZsmTJQoEsWbJkyUKBLFmyZMlCgSxZsmTJQoEsWbJkyUKBLFnvFp4t6yugc3LNAAAAAElFTkSuQmCC";

// Minimal blank PDF (base64 encoded)
const SAMPLE_PDF_BASE64 = Buffer.from(
  `%PDF-1.0
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000052 00000 n
0000000101 00000 n
trailer<</Size 4/Root 1 0 R>>
startxref
178
%%EOF`
).toString("base64");

// =============================================================================
// Example 1: Image from Base64 String
// =============================================================================
// Use this when you have image data as a base64 string, e.g., from:
// - A database blob
// - An API response
// - A data URL (strip the "data:image/png;base64," prefix first)

async function imageFromBase64() {
  console.log("=== Example 1: Image from Base64 ===\n");
  console.log("Use case: When you have image data as a base64 string\n");

  const client = createClaudeClient();

  const message = await client.messages.create({
    model: "claude-sonnet-4-20250514",
    max_tokens: 256,
    messages: [
      {
        role: "user",
        content: [
          // Image block - must come before or after text
          {
            type: "image",
            source: {
              type: "base64",
              media_type: "image/png", // Also supports: image/jpeg, image/gif, image/webp
              data: SAMPLE_PNG_BASE64,
            },
          },
          // Text block - your question about the image
          {
            type: "text",
            text: "What color is this image? Reply in one word.",
          },
        ],
      },
    ],
  });

  // Extract text response
  for (const block of message.content) {
    if (block.type === "text") {
      console.log("Response:", block.text);
    }
  }
}

// =============================================================================
// Example 2: Image from File
// =============================================================================
// Use this when loading an image from the filesystem

async function imageFromFile() {
  console.log("\n=== Example 2: Image from File ===\n");
  console.log("Use case: When loading an image from the filesystem\n");

  // Load image from file and convert to base64
  const testImagePath = join(__dirname, "test-image.png");
  let imageData: string;
  let mediaType = "image/png";

  if (existsSync(testImagePath)) {
    const buffer = readFileSync(testImagePath);
    imageData = buffer.toString("base64");
    console.log(`Loaded: ${testImagePath}`);
  } else {
    console.log("No test-image.png found, using sample image");
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
              media_type: mediaType,
              data: imageData,
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

// =============================================================================
// Example 3: Image with Streaming
// =============================================================================
// Use streaming for real-time output, useful for longer responses

async function imageWithStreaming() {
  console.log("\n=== Example 3: Image with Streaming ===\n");
  console.log("Use case: Real-time output for longer responses\n");

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
            text: "What color is this image? Reply in one word.",
          },
        ],
      },
    ],
  });

  // Stream text as it arrives
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

// =============================================================================
// Example 4: PDF Document
// =============================================================================
// Use "document" type for PDFs. Same pattern as images.

async function pdfDocument() {
  console.log("\n=== Example 4: PDF Document ===\n");
  console.log("Use case: Analyzing PDF documents\n");

  // Load PDF from file or use sample
  const testPdfPath = join(__dirname, "test.pdf");
  let pdfData: string;

  if (existsSync(testPdfPath)) {
    const buffer = readFileSync(testPdfPath);
    pdfData = buffer.toString("base64");
    console.log(`Loaded: ${testPdfPath}`);
  } else {
    console.log("No test.pdf found, using sample blank PDF");
    pdfData = SAMPLE_PDF_BASE64;
  }

  const client = createClaudeClient();

  const message = await client.messages.create({
    model: "claude-sonnet-4-20250514",
    max_tokens: 256,
    messages: [
      {
        role: "user",
        content: [
          // Use "document" type for PDFs
          {
            type: "document",
            source: {
              type: "base64",
              media_type: "application/pdf",
              data: pdfData,
            },
          },
          {
            type: "text",
            text: "Summarize this PDF in one sentence.",
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

// =============================================================================
// Example 5: Multiple Images
// =============================================================================
// You can include multiple images in a single message

async function multipleImages() {
  console.log("\n=== Example 5: Multiple Images ===\n");
  console.log("Use case: Comparing or analyzing multiple images\n");

  const client = createClaudeClient();

  const message = await client.messages.create({
    model: "claude-sonnet-4-20250514",
    max_tokens: 256,
    messages: [
      {
        role: "user",
        content: [
          // First image
          {
            type: "image",
            source: {
              type: "base64",
              media_type: "image/png",
              data: SAMPLE_PNG_BASE64,
            },
          },
          // Second image (same image for demo, but could be different)
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
            text: "Are these two images the same color? Reply yes or no.",
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

// =============================================================================
// Main
// =============================================================================

async function main() {
  console.log("╔════════════════════════════════════════════════════════════╗");
  console.log("║          Claude Code SDK - Multimodal Examples             ║");
  console.log("╚════════════════════════════════════════════════════════════╝\n");

  try {
    await imageFromBase64();
    await imageFromFile();
    await imageWithStreaming();
    await pdfDocument();
    await multipleImages();

    console.log("═".repeat(60));
    console.log("All examples completed!");
  } catch (error) {
    console.error("Error:", error);
    process.exit(1);
  }
}

main();
