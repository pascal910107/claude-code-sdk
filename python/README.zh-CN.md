# claude-code-sdk (Python)

Claude Code CLI 的 Anthropic SDK 相容層。

使用熟悉的 Anthropic SDK 介面，同時利用 Claude Code 訂閱額度取代 API 額度。

> **注意：** TypeScript/Node.js 版本請參考[根目錄 README](../README.zh-CN.md)。

## 安裝

```bash
# Clone 專案
git clone https://github.com/pascal910107/claude-code-sdk.git

# 在你的專案中，用絕對路徑安裝
cd /path/to/your-project
pip install -e /path/to/claude-code-sdk/python

# 包含 Anthropic SDK（建議）
pip install -e "/path/to/claude-code-sdk/python[anthropic]"
```

## 前置需求

- 已安裝並登入 Claude Code CLI（`claude` 指令可用）
- Python 3.10+

## 使用方式

### 基本用法

```python
from claude_code_sdk import create_claude_client

client = create_claude_client()

message = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[{"role": "user", "content": "你好，Claude！"}]
)

print(message.content[0].text)
```

### 串流

```python
from claude_code_sdk import create_claude_client

client = create_claude_client()

with client.messages.stream(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[{"role": "user", "content": "寫一首關於程式的俳句"}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

### 非同步用法

```python
import asyncio
from claude_code_sdk import create_async_claude_client

async def main():
    client = create_async_claude_client()

    message = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": "你好！"}]
    )
    print(message.content[0].text)

asyncio.run(main())
```

### 多輪對話

```python
from claude_code_sdk import create_claude_client

client = create_claude_client()
messages = []

# 第一輪
messages.append({"role": "user", "content": "我叫小張。"})
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=messages
)
messages.append({"role": "assistant", "content": response.content[0].text})

# 第二輪 - Claude 記得上下文
messages.append({"role": "user", "content": "我叫什麼名字？"})
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=messages
)
print(response.content[0].text)  # "你叫小張。"
```

## 設定

```python
from claude_code_sdk import create_claude_client

client = create_claude_client(
    # Claude Code CLI 的工作目錄
    cwd="/path/to/project",

    # 權限模式："auto"、"acceptEdits"、"plan" 或 "ask"
    permission_mode="auto",

    # claude 執行檔的自訂路徑
    binary_path="/usr/local/bin/claude",

    # 逾時時間（毫秒，預設：120000）
    timeout_ms=300000,
)
```

### 權限模式

- `"auto"` - 自動核准所有工具執行（預設，使用 `--dangerously-skip-permissions`）
- `"acceptEdits"` - 自動核准檔案編輯，其他工具需確認
- `"plan"` - 規劃模式，較為嚴格
- `"ask"` - 每次工具使用都需確認

## 運作原理

此 SDK 建立一個使用自訂 `httpx` transport 的 Anthropic client，攔截 API 請求並轉送至 Claude Code CLI。這讓你可以：

1. 使用 Claude Code 訂閱額度取代 API 額度
2. 利用 Claude Code 的工具執行能力
3. 維持與現有 Anthropic SDK 程式碼的相容性

## 支援功能

| 功能 | 狀態 |
|------|------|
| 文字對話 | 支援 |
| 串流回應 | 支援 |
| 多輪對話 | 支援 |
| System Prompt | 支援 |
| 非同步支援 | 支援 |
| 圖片/PDF | 不支援（CLI 限制）|
| 自訂 Tools | 不支援（CLI 限制）|

## 授權條款

MIT
