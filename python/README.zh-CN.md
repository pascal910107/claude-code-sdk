# claude-code-sdk (Python)

Claude Code CLI 的 Anthropic SDK 相容層。

> **注意：** TypeScript/Node.js 版本請參考[根目錄 README](../README.zh-CN.md)。

## 前置需求

- 已安裝並登入 Claude Code CLI（`claude` 指令可用）
- Python 3.10+

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

## 快速開始

```python
from claude_code_sdk import create_claude_client

client = create_claude_client()

message = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[{"role": "user", "content": "你好！"}]
)

print(message.content[0].text)
```

## 非同步用法

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

## 設定

```python
client = create_claude_client(
    cwd="/path/to/project",       # 工作目錄
    permission_mode="auto",        # "auto" | "acceptEdits" | "plan" | "ask"
    binary_path="claude",          # CLI 路徑
    timeout_ms=120000,             # 逾時時間（毫秒，預設 2 分鐘）
)
```

| 權限模式 | 行為 |
|----------|------|
| `auto`（預設）| 跳過所有權限確認 |
| `acceptEdits` | 自動接受檔案編輯 |
| `plan` | 僅規劃，不執行 |
| `ask` | 每個操作都需確認 |

## 支援功能

| 功能 | 狀態 |
|------|------|
| 文字訊息 | ✓ |
| 串流 | ✓ |
| 多輪對話 | ✓ |
| System Prompt | ✓ |
| 非同步支援 | ✓ |
| 圖片（base64）| ✓ |
| PDF（base64）| ✓ |
| 自訂 Tools | ✗ |

## 範例

完整範例請參考 [`examples/`](./examples/)：

- [`basic_usage.py`](./examples/basic_usage.py) — 文字、串流、多輪對話、非同步
- [`multimodal_usage.py`](./examples/multimodal_usage.py) — 圖片與 PDF 輸入

```bash
python examples/basic_usage.py
python examples/multimodal_usage.py
```

## 授權條款

MIT
