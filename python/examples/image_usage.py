#!/usr/bin/env python3
"""Image usage examples for claude-code-sdk."""

import base64
from pathlib import Path

# Sample 1x1 red PNG image (base64 encoded)
SAMPLE_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
)


def get_text_response(message) -> str:
    """Extract text from message content blocks."""
    texts = []
    for block in message.content:
        if block.type == "text":
            texts.append(block.text)
    return " ".join(texts) if texts else "(no text response)"


def image_from_base64():
    """Send an image using base64 encoding."""
    from claude_code_sdk import create_claude_client

    print("=== Image from Base64 ===\n")

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
    )

    print(f"Response: {get_text_response(message)}")


def image_from_file():
    """Load an image from file and send it."""
    from claude_code_sdk import create_claude_client

    print("\n=== Image from File ===\n")

    # Check if test image exists
    test_image_path = Path(__file__).parent / "test-image.png"

    if test_image_path.exists():
        with open(test_image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        print(f"Loaded image from: {test_image_path}")
    else:
        print("No test image found, using sample image")
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
                        "text": "Describe this image briefly.",
                    },
                ],
            }
        ],
    )

    print(f"Response: {get_text_response(message)}")


def image_with_streaming():
    """Stream a response with image input."""
    from claude_code_sdk import create_claude_client

    print("\n=== Image with Streaming ===\n")

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
                        "text": "What color is this image? Explain in a few words.",
                    },
                ],
            }
        ],
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
    print("\n")


def main():
    """Run all examples."""
    print("=" * 50)
    print("Claude Code SDK - Image Examples")
    print("=" * 50)
    print()

    image_from_base64()
    image_from_file()
    image_with_streaming()

    print("=" * 50)
    print("All examples completed!")
    print("=" * 50)


if __name__ == "__main__":
    main()
