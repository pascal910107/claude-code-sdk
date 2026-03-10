# claude-code-sdk

用 Claude Code 訂閱額度取代 Anthropic API，**不需要 API Key**。

Drop-in replacement，API 與官方 Anthropic SDK 完全相同。

> **注意：** 這是個人工具，未發布到 npm。如需官方程式化存取方式，請參考 [@anthropic-ai/claude-agent-sdk](https://www.npmjs.com/package/@anthropic-ai/claude-agent-sdk)。

## 前置需求

- 已安裝 Claude Code CLI：`npm install -g @anthropic-ai/claude-code`
- 已登入：`claude login`

## 安裝

Clone 並在本地 link：

```bash
# Clone 專案
git clone https://github.com/pascal910107/claude-code-sdk.git
cd claude-code-sdk

# 安裝依賴
npm install

# 建置
npm run build

# 全域 link
npm link

# 在你的專案中 link 此套件
cd /path/to/your-project
npm link claude-code-sdk
npm install @anthropic-ai/sdk
```

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
  cwd: '/path/to/project',      // 工作目錄
  permissionMode: 'auto',        // 'auto' | 'acceptEdits' | 'plan' | 'ask'
  binaryPath: 'claude',          // CLI 路徑
  timeoutMs: 120000,             // 逾時時間（毫秒，預設 2 分鐘）
});
```

### 權限模式

| 模式 | 行為 |
|------|------|
| `auto`（預設）| 跳過所有權限確認，自動執行 |
| `acceptEdits` | 自動接受檔案編輯，其他操作可能需要確認 |
| `plan` | 僅規劃，不實際執行 |
| `ask` | 每個操作都需要確認（不建議用於 SDK）|

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
