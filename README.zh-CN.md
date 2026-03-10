# claude-code-sdk

用 Claude Code 訂閱額度取代 Anthropic API，**不需要 API Key**。

Drop-in replacement，API 與官方 Anthropic SDK 完全相同。

## 安裝

```bash
npm install claude-code-sdk @anthropic-ai/sdk
```

前置需求：
- 已安裝 Claude Code CLI：`npm install -g @anthropic-ai/claude-code`
- 已登入：`claude login`

## 快速開始

```typescript
import { createClaudeClient } from 'claude-code-sdk';

const client = createClaudeClient();

// 與官方 Anthropic SDK 完全相同的 API
const message = await client.messages.create({
  model: 'claude-sonnet-4-20250514',
  max_tokens: 1024,
  messages: [{ role: 'user', content: '你好！' }],
});

console.log(message.content[0].text);
```

## 串流

```typescript
const stream = client.messages.stream({
  model: 'claude-sonnet-4-20250514',
  max_tokens: 1024,
  messages: [{ role: 'user', content: '說一個故事' }],
});

for await (const event of stream) {
  if (event.type === 'content_block_delta' && event.delta.type === 'text_delta') {
    process.stdout.write(event.delta.text);
  }
}
```

## 多輪對話

```typescript
const msg1 = await client.messages.create({
  model: 'claude-sonnet-4-20250514',
  max_tokens: 128,
  messages: [{ role: 'user', content: '我叫小張' }],
});

const msg2 = await client.messages.create({
  model: 'claude-sonnet-4-20250514',
  max_tokens: 128,
  messages: [
    { role: 'user', content: '我叫小張' },
    { role: 'assistant', content: msg1.content[0].text },
    { role: 'user', content: '我叫什麼名字？' },
  ],
});
// Claude 會回答「小張」
```

## 設定選項

```typescript
const client = createClaudeClient({
  cwd: '/path/to/project',     // 工作目錄
  permissionMode: 'auto',       // 'auto' | 'acceptEdits' | 'plan' | 'ask'
  binaryPath: 'claude',         // CLI 路徑
});
```

## 支援功能

| 功能 | 狀態 |
|------|------|
| 文字對話 | 支援 |
| 串流回應 | 支援 |
| 多輪對話 | 支援 |
| System Prompt | 支援 |
| 圖片/PDF | 不支援（CLI 限制）|
| 自訂 Tools | 不支援（CLI 限制）|

## 運作原理

攔截 Anthropic SDK 的 fetch 呼叫，將請求轉送至 Claude CLI：

```
client.messages.create()
       ↓
Anthropic SDK 內部呼叫 fetch
       ↓
攔截並轉換為 CLI 指令
       ↓
spawn('claude', ['--print', ...])
       ↓
CLI 輸出轉換回 Anthropic 格式
```

## 授權條款

MIT
