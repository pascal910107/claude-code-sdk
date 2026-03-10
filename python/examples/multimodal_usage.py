#!/usr/bin/env python3
"""
Multimodal Usage Examples - Images and PDFs

This example demonstrates how to send images and PDF documents to Claude
using the same API format as the official Anthropic SDK.

Run: python examples/multimodal_usage.py
"""

import base64
from pathlib import Path

# =============================================================================
# Test Data
# =============================================================================

# Sample 100x100 red PNG image (base64 encoded)
# In real usage, you would load this from a file or receive it from an API
SAMPLE_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAGQAAABkCAIAAAD/gAIDAAAAkElEQVR42u3QMQ0AAAjAsPk3DRb4eJpU"
    "QZviSIEsWbJkyUKBLFmyZMlCgSxZsmTJQoEsWbJkyUKBLFmyZMlCgSxZsmTJQoEsWbJkyUKBLFmyZMlC"
    "gSxZsmTJQoEsWbJkyUKBLFmyZMlCgSxZsmTJQoEsWbJkyUKBLFmyZMlCgSxZsmTJQoEsWbJkyUKBLFnv"
    "Fp4t6yugc3LNAAAAAElFTkSuQmCC"
)

# Minimal blank PDF (base64 encoded)
SAMPLE_PDF_BASE64 = base64.b64encode(
    b"""%PDF-1.0
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
%%EOF"""
).decode("utf-8")


def get_text_response(message) -> str:
    """Extract text from message content blocks."""
    texts = []
    for block in message.content:
        if block.type == "text":
            texts.append(block.text)
    return " ".join(texts) if texts else "(no text response)"


# =============================================================================
# Example 1: Image from Base64 String
# =============================================================================
# Use this when you have image data as a base64 string, e.g., from:
# - A database blob
# - An API response
# - A data URL (strip the "data:image/png;base64," prefix first)


def image_from_base64():
    """Send an image using base64 encoding."""
    from claude_code_sdk import create_claude_client

    print("=== Example 1: Image from Base64 ===\n")
    print("Use case: When you have image data as a base64 string\n")

    client = create_claude_client()

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=256,
        messages=[
            {
                "role": "user",
                "content": [
                    # Image block - must come before or after text
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",  # Also: image/jpeg, image/gif, image/webp
                            "data": SAMPLE_PNG_BASE64,
                        },
                    },
                    # Text block - your question about the image
                    {
                        "type": "text",
                        "text": "What color is this image? Reply in one word.",
                    },
                ],
            }
        ],
    )

    print(f"Response: {get_text_response(message)}")


# =============================================================================
# Example 2: Image from File
# =============================================================================
# Use this when loading an image from the filesystem


def image_from_file():
    """Load an image from file and send it."""
    from claude_code_sdk import create_claude_client

    print("\n=== Example 2: Image from File ===\n")
    print("Use case: When loading an image from the filesystem\n")

    # Load image from file and convert to base64
    test_image_path = Path(__file__).parent / "test-image.png"

    if test_image_path.exists():
        with open(test_image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        print(f"Loaded: {test_image_path}")
    else:
        print("No test-image.png found, using sample image")
        image_data = SAMPLE_PNG_BASE64

    client = create_claude_client()

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=256,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": "What color is this image? Reply in one word.",
                    },
                ],
            }
        ],
    )

    print(f"Response: {get_text_response(message)}")


# =============================================================================
# Example 3: Image with Streaming
# =============================================================================
# Use streaming for real-time output, useful for longer responses


def image_with_streaming():
    """Stream a response with image input."""
    from claude_code_sdk import create_claude_client

    print("\n=== Example 3: Image with Streaming ===\n")
    print("Use case: Real-time output for longer responses\n")

    client = create_claude_client()

    print("Response: ", end="", flush=True)
    with client.messages.stream(
        model="claude-sonnet-4-20250514",
        max_tokens=256,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": SAMPLE_PNG_BASE64,
                        },
                    },
                    {
                        "type": "text",
                        "text": "What color is this image? Reply in one word.",
                    },
                ],
            }
        ],
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
    print("\n")


# =============================================================================
# Example 4: PDF Document
# =============================================================================
# Use "document" type for PDFs. Same pattern as images.


def pdf_document():
    """Send a PDF document."""
    from claude_code_sdk import create_claude_client

    print("\n=== Example 4: PDF Document ===\n")
    print("Use case: Analyzing PDF documents\n")

    # Load PDF from file or use sample
    test_pdf_path = Path(__file__).parent / "test.pdf"

    if test_pdf_path.exists():
        with open(test_pdf_path, "rb") as f:
            pdf_data = base64.b64encode(f.read()).decode("utf-8")
        print(f"Loaded: {test_pdf_path}")
    else:
        print("No test.pdf found, using sample blank PDF")
        pdf_data = SAMPLE_PDF_BASE64

    client = create_claude_client()

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=256,
        messages=[
            {
                "role": "user",
                "content": [
                    # Use "document" type for PDFs
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": "Summarize this PDF in one sentence.",
                    },
                ],
            }
        ],
    )

    print(f"Response: {get_text_response(message)}")


# =============================================================================
# Example 5: Multiple Images
# =============================================================================
# You can include multiple images in a single message


def multiple_images():
    """Send multiple images in one message."""
    from claude_code_sdk import create_claude_client

    print("\n=== Example 5: Multiple Images ===\n")
    print("Use case: Comparing or analyzing multiple images\n")

    client = create_claude_client()

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=256,
        messages=[
            {
                "role": "user",
                "content": [
                    # First image
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": SAMPLE_PNG_BASE64,
                        },
                    },
                    # Second image (same for demo, could be different)
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": SAMPLE_PNG_BASE64,
                        },
                    },
                    {
                        "type": "text",
                        "text": "Are these two images the same color? Reply yes or no.",
                    },
                ],
            }
        ],
    )

    print(f"Response: {get_text_response(message)}")


# =============================================================================
# Main
# =============================================================================


def main():
    """Run all examples."""
    print("╔" + "═" * 58 + "╗")
    print("║" + "Claude Code SDK - Multimodal Examples".center(58) + "║")
    print("╚" + "═" * 58 + "╝")
    print()

    image_from_base64()
    image_from_file()
    image_with_streaming()
    pdf_document()
    multiple_images()

    print("═" * 60)
    print("All examples completed!")


if __name__ == "__main__":
    main()
