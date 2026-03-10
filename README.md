# claude-code-sdk

Use your Claude Code subscription instead of Anthropic API credits — **no API key required**.

Drop-in replacement with the same API as the official Anthropic SDK.

> **Note:** This is a personal tool, not published to npm. For official programmatic access, see [@anthropic-ai/claude-agent-sdk](https://www.npmjs.com/package/@anthropic-ai/claude-agent-sdk).

## Language Support

| Language | Location | Status |
|----------|----------|--------|
| TypeScript/Node.js | This directory | Stable |
| Python | [python/](./python/) | Stable |

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

## Configuration Options

```typescript
const client = createClaudeClient({
  cwd: '/path/to/project',      // Working directory
  permissionMode: 'auto',        // 'auto' | 'acceptEdits' | 'plan' | 'ask'
  binaryPath: 'claude',          // CLI path
  timeoutMs: 120000,             // Timeout in milliseconds (default: 2 minutes)
});
```

| Permission Mode | Behavior |
|-----------------|----------|
| `auto` (default) | Skips all permission prompts, executes automatically |
| `acceptEdits` | Auto-accepts file edits, other operations may need confirmation |
| `plan` | Planning only, no actual execution |
| `ask` | Requires confirmation for each operation (not recommended for SDK use) |

## Supported Features

| Feature | Status |
|---------|--------|
| Text messages | ✓ |
| Streaming | ✓ |
| Multi-turn conversations | ✓ |
| System prompt | ✓ |
| Images (base64) | ✓ |
| PDF (base64) | ✓ |
| Custom tools | ✗ |

## Examples

See [`examples/`](./examples/) for complete examples:

- [`basic-usage.ts`](./examples/basic-usage.ts) — Text, streaming, multi-turn
- [`multimodal-usage.ts`](./examples/multimodal-usage.ts) — Image and PDF input

```bash
npx tsx examples/basic-usage.ts
npx tsx examples/multimodal-usage.ts
```

## How It Works

```
Anthropic SDK → fetch() → [Intercepted] → CLI stdin → Claude Code → Response
```

## License

MIT
