# claude-code-sdk

Use your Claude Code subscription instead of Anthropic API credits — **no API key required**.

Drop-in replacement with the same API as the official Anthropic SDK.

> **Note:** This is a personal tool, not published to npm. For official programmatic access, see [@anthropic-ai/claude-agent-sdk](https://www.npmjs.com/package/@anthropic-ai/claude-agent-sdk).

## Prerequisites

- Claude Code CLI installed: `npm install -g @anthropic-ai/claude-code`
- Logged in: `claude login`

## Installation

Clone and link locally:

```bash
# Clone the repository
git clone https://github.com/pascal910107/claude-code-sdk.git
cd claude-code-sdk

# Install dependencies
npm install

# Build the package
npm run build

# Link globally
npm link

# In your project, link the package
cd /path/to/your-project
npm link claude-code-sdk
npm install @anthropic-ai/sdk
```

## Quick Start

```typescript
import { createClaudeClient } from 'claude-code-sdk';

const client = createClaudeClient();

// Same API as the official Anthropic SDK
const message = await client.messages.create({
  model: 'claude-sonnet-4-20250514',
  max_tokens: 1024,
  messages: [{ role: 'user', content: 'Hello!' }],
});

console.log(message.content[0].text);
```

## Streaming

```typescript
const stream = client.messages.stream({
  model: 'claude-sonnet-4-20250514',
  max_tokens: 1024,
  messages: [{ role: 'user', content: 'Tell me a story' }],
});

for await (const event of stream) {
  if (event.type === 'content_block_delta' && event.delta.type === 'text_delta') {
    process.stdout.write(event.delta.text);
  }
}
```

## Multi-turn Conversations

```typescript
const msg1 = await client.messages.create({
  model: 'claude-sonnet-4-20250514',
  max_tokens: 128,
  messages: [{ role: 'user', content: 'My name is Alice' }],
});

const msg2 = await client.messages.create({
  model: 'claude-sonnet-4-20250514',
  max_tokens: 128,
  messages: [
    { role: 'user', content: 'My name is Alice' },
    { role: 'assistant', content: msg1.content[0].text },
    { role: 'user', content: 'What is my name?' },
  ],
});
// Claude will respond with "Alice"
```

## Configuration Options

```typescript
const client = createClaudeClient({
  cwd: '/path/to/project',      // Working directory
  permissionMode: 'auto',        // 'auto' | 'acceptEdits' | 'plan' | 'ask'
  binaryPath: 'claude',          // CLI path
  timeoutMs: 120000,             // Timeout in milliseconds (default: 2 minutes)
});
```

### Permission Modes

| Mode | Behavior |
|------|----------|
| `auto` (default) | Skips all permission prompts, executes automatically |
| `acceptEdits` | Auto-accepts file edits, other operations may need confirmation |
| `plan` | Planning only, no actual execution |
| `ask` | Requires confirmation for each operation (not recommended for SDK use) |

## Supported Features

| Feature | Status |
|---------|--------|
| Text conversations | Supported |
| Streaming responses | Supported |
| Multi-turn conversations | Supported |
| System prompt | Supported |
| Images/PDF | Not supported (CLI limitation) |
| Custom tools | Not supported (CLI limitation) |

## How It Works

Intercepts the Anthropic SDK's fetch calls and routes requests through the Claude CLI:

```
client.messages.create()
       ↓
Anthropic SDK internally calls fetch
       ↓
We intercept and convert to CLI command
       ↓
spawn('claude', ['--print', ...])
       ↓
CLI output converted back to Anthropic format
```

## License

MIT
