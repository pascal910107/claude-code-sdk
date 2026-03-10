"""Custom httpx Transport for routing requests through Claude CLI."""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import time
from typing import TYPE_CHECKING, Any, Iterator

import httpx

from ..parser import create_parser_state, parse_line
from .sessions import SessionStore
from .transform import request_to_cli_args

if TYPE_CHECKING:
    from ..types import PermissionMode

DEFAULT_TIMEOUT_MS = 120_000


class CLITransport(httpx.BaseTransport):
    """
    Synchronous httpx Transport that routes Anthropic API requests through Claude CLI.
    """

    def __init__(
        self,
        *,
        cwd: str | None = None,
        permission_mode: PermissionMode = "auto",
        binary_path: str = "claude",
        timeout_ms: int = DEFAULT_TIMEOUT_MS,
        sessions: SessionStore | None = None,
    ) -> None:
        self.cwd = cwd or os.getcwd()
        self.permission_mode = permission_mode
        self.binary_path = binary_path
        self.timeout_ms = timeout_ms
        self.sessions = sessions or SessionStore()

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        """Handle an outgoing request."""
        url = str(request.url)

        # Only intercept /v1/messages endpoint
        if url.endswith("/v1/messages"):
            return self._handle_messages_request(request)

        # Other endpoints - return error (shouldn't happen in normal usage)
        return httpx.Response(
            status_code=404,
            content=b'{"error": "Endpoint not supported by CLI transport"}',
            headers={"Content-Type": "application/json"},
        )

    def _handle_messages_request(self, request: httpx.Request) -> httpx.Response:
        """Handle a messages.create request."""
        body = json.loads(request.content)
        is_streaming = body.get("stream", False)

        # Get session ID for multi-turn conversations
        session_id = self.sessions.get_session_id(body.get("messages", []))

        # Build CLI arguments
        cli_args = request_to_cli_args(
            body,
            session_id,
            permission_mode=self.permission_mode,
        )

        if is_streaming:
            return self._create_streaming_response(cli_args, body)
        else:
            return self._create_non_streaming_response(cli_args, body)

    def _create_streaming_response(
        self, cli_args: list[str], request_body: dict[str, Any]
    ) -> httpx.Response:
        """Create a streaming SSE response."""
        process = subprocess.Popen(
            [self.binary_path, *cli_args],
            cwd=self.cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            env={**os.environ, "NO_COLOR": "1"},
        )

        def generate_sse() -> Iterator[bytes]:
            """Generate SSE events from CLI output."""
            parser_state = create_parser_state()
            message_id = f"msg_{int(time.time() * 1000)}"
            output_tokens = 0
            content_block_index = 0
            current_block_type: str | None = None

            def send_event(event_type: str, data: dict[str, Any]) -> bytes:
                return f"event: {event_type}\ndata: {json.dumps(data)}\n\n".encode()

            # Send initial message_start event
            yield send_event(
                "message_start",
                {
                    "type": "message_start",
                    "message": {
                        "id": message_id,
                        "type": "message",
                        "role": "assistant",
                        "content": [],
                        "model": request_body.get("model", ""),
                        "stop_reason": None,
                        "stop_sequence": None,
                        "usage": {"input_tokens": 0, "output_tokens": 0},
                    },
                },
            )

            assert process.stdout is not None
            for line_bytes in process.stdout:
                line = line_bytes.decode("utf-8")
                events = parse_line(line, parser_state)

                # Update session ID from parser state
                if parser_state.session_id:
                    self.sessions.update_session(
                        request_body.get("messages", []),
                        parser_state.session_id,
                    )

                for event in events:
                    if event.type == "text":
                        # Start new text block if needed
                        if current_block_type != "text":
                            if current_block_type is not None:
                                yield send_event(
                                    "content_block_stop",
                                    {
                                        "type": "content_block_stop",
                                        "index": content_block_index - 1,
                                    },
                                )
                            yield send_event(
                                "content_block_start",
                                {
                                    "type": "content_block_start",
                                    "index": content_block_index,
                                    "content_block": {"type": "text", "text": ""},
                                },
                            )
                            current_block_type = "text"

                        yield send_event(
                            "content_block_delta",
                            {
                                "type": "content_block_delta",
                                "index": content_block_index,
                                "delta": {"type": "text_delta", "text": event.content},
                            },
                        )

                    elif event.type == "thinking":
                        # Handle thinking blocks
                        if current_block_type != "thinking":
                            if current_block_type is not None:
                                yield send_event(
                                    "content_block_stop",
                                    {
                                        "type": "content_block_stop",
                                        "index": content_block_index - 1,
                                    },
                                )
                            content_block_index += 1
                            yield send_event(
                                "content_block_start",
                                {
                                    "type": "content_block_start",
                                    "index": content_block_index,
                                    "content_block": {"type": "thinking", "thinking": ""},
                                },
                            )
                            current_block_type = "thinking"

                        yield send_event(
                            "content_block_delta",
                            {
                                "type": "content_block_delta",
                                "index": content_block_index,
                                "delta": {"type": "thinking_delta", "thinking": event.content},
                            },
                        )

                    elif event.type == "tool_use":
                        # Close previous block
                        if current_block_type is not None:
                            yield send_event(
                                "content_block_stop",
                                {
                                    "type": "content_block_stop",
                                    "index": content_block_index,
                                },
                            )
                            content_block_index += 1

                        yield send_event(
                            "content_block_start",
                            {
                                "type": "content_block_start",
                                "index": content_block_index,
                                "content_block": {
                                    "type": "tool_use",
                                    "id": event.id,
                                    "name": event.name,
                                    "input": event.input or {},
                                },
                            },
                        )
                        current_block_type = "tool_use"

                    elif event.type == "complete":
                        output_tokens = event.output_tokens

                    elif event.type == "error":
                        yield send_event(
                            "error",
                            {
                                "type": "error",
                                "error": {"type": "api_error", "message": event.message},
                            },
                        )

            # Close final content block
            if current_block_type is not None:
                yield send_event(
                    "content_block_stop",
                    {
                        "type": "content_block_stop",
                        "index": content_block_index,
                    },
                )

            # Send message_delta and message_stop
            yield send_event(
                "message_delta",
                {
                    "type": "message_delta",
                    "delta": {"stop_reason": "end_turn", "stop_sequence": None},
                    "usage": {"output_tokens": output_tokens},
                },
            )

            yield send_event("message_stop", {"type": "message_stop"})

            process.wait()

        return httpx.Response(
            status_code=200,
            headers={
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
            stream=httpx.ByteStream(b"".join(generate_sse())),
        )

    def _create_non_streaming_response(
        self, cli_args: list[str], request_body: dict[str, Any]
    ) -> httpx.Response:
        """Create a non-streaming response."""
        process = subprocess.Popen(
            [self.binary_path, *cli_args],
            cwd=self.cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            env={**os.environ, "NO_COLOR": "1"},
        )

        parser_state = create_parser_state()
        content_blocks: list[dict[str, Any]] = []
        current_text = ""
        input_tokens = 0
        output_tokens = 0
        error_message: str | None = None

        try:
            stdout, stderr = process.communicate(timeout=self.timeout_ms / 1000)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            return httpx.Response(
                status_code=408,
                content=json.dumps(
                    {
                        "type": "error",
                        "error": {
                            "type": "api_error",
                            "message": f"CLI timeout after {self.timeout_ms}ms",
                        },
                    }
                ).encode(),
                headers={"Content-Type": "application/json"},
            )

        for line in stdout.decode("utf-8").splitlines():
            events = parse_line(line, parser_state)

            if parser_state.session_id:
                self.sessions.update_session(
                    request_body.get("messages", []),
                    parser_state.session_id,
                )

            for event in events:
                if event.type == "text":
                    current_text += event.content
                elif event.type == "tool_use":
                    # Flush accumulated text before tool
                    if current_text:
                        content_blocks.append({"type": "text", "text": current_text})
                        current_text = ""
                    content_blocks.append(
                        {
                            "type": "tool_use",
                            "id": event.id,
                            "name": event.name,
                            "input": event.input or {},
                        }
                    )
                elif event.type == "complete":
                    input_tokens = event.input_tokens
                    output_tokens = event.output_tokens
                elif event.type == "error":
                    error_message = event.message

        # Flush remaining text
        if current_text:
            content_blocks.append({"type": "text", "text": current_text})

        if error_message:
            return httpx.Response(
                status_code=400,
                content=json.dumps(
                    {
                        "type": "error",
                        "error": {"type": "api_error", "message": error_message},
                    }
                ).encode(),
                headers={"Content-Type": "application/json"},
            )

        response_data = {
            "id": f"msg_{int(time.time() * 1000)}",
            "type": "message",
            "role": "assistant",
            "content": content_blocks,
            "model": request_body.get("model", ""),
            "stop_reason": "end_turn",
            "stop_sequence": None,
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            },
        }

        return httpx.Response(
            status_code=200,
            content=json.dumps(response_data).encode(),
            headers={"Content-Type": "application/json"},
        )


class AsyncCLITransport(httpx.AsyncBaseTransport):
    """
    Asynchronous httpx Transport that routes Anthropic API requests through Claude CLI.
    """

    def __init__(
        self,
        *,
        cwd: str | None = None,
        permission_mode: PermissionMode = "auto",
        binary_path: str = "claude",
        timeout_ms: int = DEFAULT_TIMEOUT_MS,
        sessions: SessionStore | None = None,
    ) -> None:
        self.cwd = cwd or os.getcwd()
        self.permission_mode = permission_mode
        self.binary_path = binary_path
        self.timeout_ms = timeout_ms
        self.sessions = sessions or SessionStore()

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        """Handle an outgoing request."""
        url = str(request.url)

        # Only intercept /v1/messages endpoint
        if url.endswith("/v1/messages"):
            return await self._handle_messages_request(request)

        # Other endpoints - return error
        return httpx.Response(
            status_code=404,
            content=b'{"error": "Endpoint not supported by CLI transport"}',
            headers={"Content-Type": "application/json"},
        )

    async def _handle_messages_request(self, request: httpx.Request) -> httpx.Response:
        """Handle a messages.create request."""
        body = json.loads(request.content)
        is_streaming = body.get("stream", False)

        # Get session ID for multi-turn conversations
        session_id = self.sessions.get_session_id(body.get("messages", []))

        # Build CLI arguments
        cli_args = request_to_cli_args(
            body,
            session_id,
            permission_mode=self.permission_mode,
        )

        if is_streaming:
            return await self._create_streaming_response(cli_args, body)
        else:
            return await self._create_non_streaming_response(cli_args, body)

    async def _create_streaming_response(
        self, cli_args: list[str], request_body: dict[str, Any]
    ) -> httpx.Response:
        """Create a streaming SSE response."""
        process = await asyncio.create_subprocess_exec(
            self.binary_path,
            *cli_args,
            cwd=self.cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            env={**os.environ, "NO_COLOR": "1"},
        )

        async def generate_sse() -> bytes:
            """Generate SSE events from CLI output."""
            parser_state = create_parser_state()
            message_id = f"msg_{int(time.time() * 1000)}"
            output_tokens = 0
            content_block_index = 0
            current_block_type: str | None = None
            result_chunks: list[bytes] = []

            def send_event(event_type: str, data: dict[str, Any]) -> bytes:
                return f"event: {event_type}\ndata: {json.dumps(data)}\n\n".encode()

            # Send initial message_start event
            result_chunks.append(
                send_event(
                    "message_start",
                    {
                        "type": "message_start",
                        "message": {
                            "id": message_id,
                            "type": "message",
                            "role": "assistant",
                            "content": [],
                            "model": request_body.get("model", ""),
                            "stop_reason": None,
                            "stop_sequence": None,
                            "usage": {"input_tokens": 0, "output_tokens": 0},
                        },
                    },
                )
            )

            assert process.stdout is not None
            async for line_bytes in process.stdout:
                line = line_bytes.decode("utf-8")
                events = parse_line(line, parser_state)

                # Update session ID from parser state
                if parser_state.session_id:
                    self.sessions.update_session(
                        request_body.get("messages", []),
                        parser_state.session_id,
                    )

                for event in events:
                    if event.type == "text":
                        if current_block_type != "text":
                            if current_block_type is not None:
                                result_chunks.append(
                                    send_event(
                                        "content_block_stop",
                                        {
                                            "type": "content_block_stop",
                                            "index": content_block_index - 1,
                                        },
                                    )
                                )
                            result_chunks.append(
                                send_event(
                                    "content_block_start",
                                    {
                                        "type": "content_block_start",
                                        "index": content_block_index,
                                        "content_block": {"type": "text", "text": ""},
                                    },
                                )
                            )
                            current_block_type = "text"

                        result_chunks.append(
                            send_event(
                                "content_block_delta",
                                {
                                    "type": "content_block_delta",
                                    "index": content_block_index,
                                    "delta": {"type": "text_delta", "text": event.content},
                                },
                            )
                        )

                    elif event.type == "thinking":
                        if current_block_type != "thinking":
                            if current_block_type is not None:
                                result_chunks.append(
                                    send_event(
                                        "content_block_stop",
                                        {
                                            "type": "content_block_stop",
                                            "index": content_block_index - 1,
                                        },
                                    )
                                )
                            content_block_index += 1
                            result_chunks.append(
                                send_event(
                                    "content_block_start",
                                    {
                                        "type": "content_block_start",
                                        "index": content_block_index,
                                        "content_block": {"type": "thinking", "thinking": ""},
                                    },
                                )
                            )
                            current_block_type = "thinking"

                        result_chunks.append(
                            send_event(
                                "content_block_delta",
                                {
                                    "type": "content_block_delta",
                                    "index": content_block_index,
                                    "delta": {"type": "thinking_delta", "thinking": event.content},
                                },
                            )
                        )

                    elif event.type == "tool_use":
                        if current_block_type is not None:
                            result_chunks.append(
                                send_event(
                                    "content_block_stop",
                                    {
                                        "type": "content_block_stop",
                                        "index": content_block_index,
                                    },
                                )
                            )
                            content_block_index += 1

                        result_chunks.append(
                            send_event(
                                "content_block_start",
                                {
                                    "type": "content_block_start",
                                    "index": content_block_index,
                                    "content_block": {
                                        "type": "tool_use",
                                        "id": event.id,
                                        "name": event.name,
                                        "input": event.input or {},
                                    },
                                },
                            )
                        )
                        current_block_type = "tool_use"

                    elif event.type == "complete":
                        output_tokens = event.output_tokens

                    elif event.type == "error":
                        result_chunks.append(
                            send_event(
                                "error",
                                {
                                    "type": "error",
                                    "error": {"type": "api_error", "message": event.message},
                                },
                            )
                        )

            # Close final content block
            if current_block_type is not None:
                result_chunks.append(
                    send_event(
                        "content_block_stop",
                        {
                            "type": "content_block_stop",
                            "index": content_block_index,
                        },
                    )
                )

            # Send message_delta and message_stop
            result_chunks.append(
                send_event(
                    "message_delta",
                    {
                        "type": "message_delta",
                        "delta": {"stop_reason": "end_turn", "stop_sequence": None},
                        "usage": {"output_tokens": output_tokens},
                    },
                )
            )

            result_chunks.append(send_event("message_stop", {"type": "message_stop"}))

            await process.wait()
            return b"".join(result_chunks)

        content = await generate_sse()

        return httpx.Response(
            status_code=200,
            headers={
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
            stream=httpx.ByteStream(content),
        )

    async def _create_non_streaming_response(
        self, cli_args: list[str], request_body: dict[str, Any]
    ) -> httpx.Response:
        """Create a non-streaming response."""
        process = await asyncio.create_subprocess_exec(
            self.binary_path,
            *cli_args,
            cwd=self.cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            env={**os.environ, "NO_COLOR": "1"},
        )

        parser_state = create_parser_state()
        content_blocks: list[dict[str, Any]] = []
        current_text = ""
        input_tokens = 0
        output_tokens = 0
        error_message: str | None = None

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout_ms / 1000,
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.communicate()
            return httpx.Response(
                status_code=408,
                content=json.dumps(
                    {
                        "type": "error",
                        "error": {
                            "type": "api_error",
                            "message": f"CLI timeout after {self.timeout_ms}ms",
                        },
                    }
                ).encode(),
                headers={"Content-Type": "application/json"},
            )

        for line in stdout.decode("utf-8").splitlines():
            events = parse_line(line, parser_state)

            if parser_state.session_id:
                self.sessions.update_session(
                    request_body.get("messages", []),
                    parser_state.session_id,
                )

            for event in events:
                if event.type == "text":
                    current_text += event.content
                elif event.type == "tool_use":
                    if current_text:
                        content_blocks.append({"type": "text", "text": current_text})
                        current_text = ""
                    content_blocks.append(
                        {
                            "type": "tool_use",
                            "id": event.id,
                            "name": event.name,
                            "input": event.input or {},
                        }
                    )
                elif event.type == "complete":
                    input_tokens = event.input_tokens
                    output_tokens = event.output_tokens
                elif event.type == "error":
                    error_message = event.message

        # Flush remaining text
        if current_text:
            content_blocks.append({"type": "text", "text": current_text})

        if error_message:
            return httpx.Response(
                status_code=400,
                content=json.dumps(
                    {
                        "type": "error",
                        "error": {"type": "api_error", "message": error_message},
                    }
                ).encode(),
                headers={"Content-Type": "application/json"},
            )

        response_data = {
            "id": f"msg_{int(time.time() * 1000)}",
            "type": "message",
            "role": "assistant",
            "content": content_blocks,
            "model": request_body.get("model", ""),
            "stop_reason": "end_turn",
            "stop_sequence": None,
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            },
        }

        return httpx.Response(
            status_code=200,
            content=json.dumps(response_data).encode(),
            headers={"Content-Type": "application/json"},
        )
