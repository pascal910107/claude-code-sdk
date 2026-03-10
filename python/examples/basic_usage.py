#!/usr/bin/env python3
"""Basic usage examples for claude-code-sdk."""

import asyncio


def basic_example():
    """Basic synchronous usage."""
    from claude_code_sdk import create_claude_client

    client = create_claude_client()

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=128,
        messages=[{"role": "user", "content": "Hello! Say hi in one sentence."}],
    )

    print("Basic example:")
    print(message.content[0].text)
    print()


def streaming_example():
    """Streaming usage."""
    from claude_code_sdk import create_claude_client

    client = create_claude_client()

    print("Streaming example:")
    with client.messages.stream(
        model="claude-sonnet-4-20250514",
        max_tokens=128,
        messages=[{"role": "user", "content": "Write a haiku about Python."}],
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
    print("\n")


def multi_turn_example():
    """Multi-turn conversation."""
    from claude_code_sdk import create_claude_client

    client = create_claude_client()
    messages: list[dict] = []

    print("Multi-turn example:")

    # First turn
    messages.append({"role": "user", "content": "My favorite color is blue."})
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=128,
        messages=messages,
    )
    assistant_msg = response.content[0].text
    messages.append({"role": "assistant", "content": assistant_msg})
    print(f"User: My favorite color is blue.")
    print(f"Assistant: {assistant_msg}")

    # Second turn - Claude should remember the context
    messages.append({"role": "user", "content": "What's my favorite color?"})
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=128,
        messages=messages,
    )
    print(f"User: What's my favorite color?")
    print(f"Assistant: {response.content[0].text}")
    print()


async def async_example():
    """Async usage."""
    from claude_code_sdk import create_async_claude_client

    client = create_async_claude_client()

    message = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=128,
        messages=[{"role": "user", "content": "Hello from async! Respond briefly."}],
    )

    print("Async example:")
    print(message.content[0].text)
    print()


def main():
    """Run all examples."""
    print("=" * 50)
    print("Claude Code SDK - Python Examples")
    print("=" * 50)
    print()

    basic_example()
    streaming_example()
    multi_turn_example()
    asyncio.run(async_example())

    print("=" * 50)
    print("All examples completed!")
    print("=" * 50)


if __name__ == "__main__":
    main()
