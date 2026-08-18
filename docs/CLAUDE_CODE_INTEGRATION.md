# omlx + Qwen3.5-35B-A3B-4bit 用于 Claude Code 集成指南

> 在本地 Mac 上部署 omlx 框架运行 Qwen3.5-35B-A3B-4bit 量化模型，通过 OpenAI 兼容 API 集成到 Claude Code

---

## 📋 目录

1. [可行性结论](#可行性结论)
2. [能力对比](#能力对比)
3. [架构设计](#架构设计)
4. [部署配置](#部署配置)
5. [使用场景](#使用场景)
6. [限制与解决方案](#限制与解决方案)
7. [故障排查](#故障排查)

---

## 可行性结论

### ✅ 结论：**可行，但有局限**

| 评估维度 | 评级 | 说明 |
|---------|------|------|
| 代码生成 | ✅ 完全支持 | 74+ tokens/s 速度 |
| 代码解释 | ✅ 完全支持 | 中文支持优秀 |
| 多轮对话 | ✅ 完全支持 | 上下文 32K-128K |
| 工具调用 | ⚠️ 部分支持 | 需 MCP 桥接 |
| 文件操作 | ⚠️ 需配置 | 需 MCP 文件系统 |
| Bash 执行 | ⚠️ 需配置 | 需 MCP Shell |
| 性价比 | ✅ 优秀 | 无 API 费用 |

---

## 能力对比

### Claude 官方 API vs Qwen3.5-35B-A3B-4bit

| 功能 | Claude 官方 | Qwen3.5-4bit | 满足度 |
|------|------------|-------------|--------|
| 代码生成 | ✅ | ✅ | ✅ |
| 代码解释 | ✅ | ✅ | ✅ |
| 多轮对话 | ✅ | ✅ | ✅ |
| 工具调用 | ✅ | ⚠️ 部分 | ⚠️ |
| 文件读写 | ✅ | ❌ 需 MCP | ❌ |
| Bash 执行 | ✅ | ❌ 需 MCP | ❌ |
| 上下文窗口 | 200K | 32K-128K | ⚠️ |
| 响应速度 | 快 | 74+ tok/s | ✅ |
| 离线使用 | ❌ | ✅ | ✅ |
| API 费用 | $$$ | 免费 | ✅ |

### 性能基准（omlx 框架）

| 测试项目 | Tokens | 耗时 | 速度 |
|---------|--------|------|------|
| 短回答 | 512 | 10.32s | 49.59 tok/s |
| 代码生成 | 512 | 6.18s | 82.82 tok/s |
| 逻辑推理 | 512 | 6.21s | 82.49 tok/s |
| 长文本 | 512 | 6.19s | 82.68 tok/s |
| **平均** | - | - | **74.39 tok/s** |

---

## 架构设计

### 部署架构

```
┌─────────────────────────────────────────────────────────────┐
│                    局域网部署架构                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐      ┌──────────────┐                     │
│  │  Mac 服务器   │      │  量化模型     │                     │
│  │  omlx serve  │◄────►│  4bit 19GB   │                     │
│  │  192.168.1.100│      │  Qwen3.5     │                     │
│  └──────┬───────┘      └──────────────┘                     │
│         │ 端口：8000                                        │
│         ▼                                                   │
│    ┌────┴────┐    ┌────┴────┐    ┌────┴────┐               │
│    │  Claude │    │  Claude │    │  Python │               │
│    │  Code 1 │    │  Code 2 │    │  Client │               │
│    └─────────┘    └─────────┘    └─────────┘               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 数据流

```
┌─────────────┐     HTTP/OpenAI API     ┌─────────────┐
│  Claude Code│ ──────────────────────► │  omlx Server│
│             │ ◄────────────────────── │             │
│             │    流式响应              │  模型推理    │
└─────────────┘                         └─────────────┘
                                               │
                                               ▼
                                      ┌─────────────┐
                                      │  Qwen3.5    │
                                      │  4bit 量化  │
                                      └─────────────┘
```

---

## 部署配置

### 环境要求

| 项目 | 要求 | 检查命令 |
|------|------|---------|
| 操作系统 | macOS 15.0+ | `sw_vers` |
| 硬件 | Apple Silicon | `sysctl -n machdep.cpu.brand_string` |
| 内存 | 16GB+ (推荐 32GB+) | `sysctl hw.memsize` |
| Python | 3.11–3.13 | `python3 --version` |
| 存储空间 | 25GB+ (模型 19GB) | `df -h ~` |

### 1. 安装 omlx

```bash
# 克隆仓库
git clone https://github.com/jundot/omlx.git
cd omlx

# 安装依赖
pip install -e ".[dev]" --break-system-packages

# 验证安装
omlx --version
```

### 2. 准备模型

```bash
# 模型位置（根据实际路径调整）
MODEL_DIR="$HOME/Qwen3.5-35B-A3B-Uncensored-HauhauCS-Aggressive/models"

# 确认模型存在
ls -la "$MODEL_DIR/Qwen3.5-35B-A3B-mlx-4bit/"
```

### 3. 启动服务器

#### 方法 A：使用启动脚本（推荐）

```bash
# 赋予执行权限
chmod +x scripts/start_server.sh

# 启动 4bit 模型服务
./scripts/start_server.sh \
  --model-type 4bit \
  --port 8000 \
  --api-key your-claude-code-key
```

#### 方法 B：直接命令

```bash
omlx serve \
  --model-dir "$HOME/Qwen3.5-35B-A3B-Uncensored-HauhauCS-Aggressive/models/Qwen3.5-35B-A3B-mlx-4bit" \
  --host 0.0.0.0 \
  --port 8000 \
  --api-key your-claude-code-key \
  --memory-guard-gb 24 \
  --paged-ssd-cache-dir ~/.omlx/cache \
  --paged-ssd-cache-max-size 50GB \
  --hot-cache-max-size 4GB \
  --log-level info
```

#### 方法 C：systemd/launchd 自动启动

```bash
# 复制配置文件
cp config/launchd.plist ~/Library/LaunchAgents/com.omlx.server.plist

# 编辑路径（根据实际情况修改）
vi ~/Library/LaunchAgents/com.omlx.server.plist

# 加载配置
launchctl load ~/Library/LaunchAgents/com.omlx.server.plist

# 查看状态
launchctl list | grep omlx
```

### 4. 验证服务

```bash
# 健康检查
curl http://localhost:8000/health

# 预期输出：{"status":"healthy", ...}（启动预加载期间返回 503 与 "loading"）

# 获取模型列表
curl http://localhost:8000/v1/models

# 访问管理面板
open http://localhost:8000/admin
```

### 5. 配置防火墙

```bash
# macOS 防火墙
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /opt/homebrew/bin/python3
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblockapp /opt/homebrew/bin/python3

# 验证端口开放
lsof -i :8000
```

---

## 使用场景

### 场景 1：代码生成与补全

```python
# 配置客户端
from openai import OpenAI

client = OpenAI(
    base_url="http://192.168.1.100:8000/v1",
    api_key="your-claude-code-key"
)

# 代码生成
response = client.chat.completions.create(
    model="Qwen3.5-35B-A3B-mlx-4bit",
    messages=[
        {"role": "user", "content": "用 Python 写一个快速排序，包含注释和测试"}
    ],
    max_tokens=1024,
    stream=True
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

### 场景 2：代码解释

```python
response = client.chat.completions.create(
    model="Qwen3.5-35B-A3B-mlx-4bit",
    messages=[
        {"role": "user", "content": """
请解释这段代码的工作原理：

def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""}
    ],
    max_tokens=512
)

print(response.choices[0].message.content)
```

### 场景 3：多轮对话教学

```python
messages = [
    {"role": "user", "content": "我想学习 Python"},
]

while True:
    user_input = input("你：")
    if user_input.lower() == "quit":
        break

    messages.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model="Qwen3.5-35B-A3B-mlx-4bit",
        messages=messages,
        max_tokens=512,
        stream=True
    )

    print("AI: ", end="")
    full_response = ""
    for chunk in response:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="")
            full_response += chunk.choices[0].delta.content
    print()

    messages.append({"role": "assistant", "content": full_response})
```

### 场景 4：批量推理

```python
import asyncio
from openai import OpenAI

client = OpenAI(
    base_url="http://192.168.1.100:8000/v1",
    api_key="your-claude-code-key"
)

async def batch_process(prompts: list):
    """批量处理多个请求"""
    async def process(prompt):
        return client.chat.completions.create(
            model="Qwen3.5-35B-A3B-mlx-4bit",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=256
        )

    tasks = [process(p) for p in prompts]
    return await asyncio.gather(*tasks)

# 使用示例
prompts = [
    "解释什么是闭包",
    "解释什么是装饰器",
    "解释什么是生成器"
]

responses = asyncio.run(batch_process(prompts))
for i, resp in enumerate(responses):
    print(f"{i+1}. {resp.choices[0].message.content[:100]}...")
```

---

## 限制与解决方案

### 限制 1：工具调用不兼容

**问题**：Claude Code 的工具调用格式与 Qwen3.5 不同

**解决方案 A**：禁用工具调用，仅用于纯文本任务

```json
{
  "features": {
    "tool_use": false
  }
}
```

**解决方案 B**：配置 MCP 桥接

```bash
# 创建 MCP 配置
cat > mcp-config.json << 'EOF'
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "~/"]
    },
    "shell": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-shell"]
    }
  }
}
EOF

# 启动 omlx 带 MCP
omlx serve --model-dir ~/models --mcp-config mcp-config.json
```

### 限制 2：上下文窗口较小

**问题**：Qwen3.5 最大 32K-128K vs Claude 200K

**解决方案**：
- 使用 `omlx` 的 SSD 缓存，支持长上下文前缀复用
- 对于超长文件，使用分段处理

```python
def process_long_context(text: str, chunk_size: int = 20000):
    """分段处理长文本"""
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    results = []
    for chunk in chunks:
        response = client.chat.completions.create(
            model="Qwen3.5-35B-A3B-mlx-4bit",
            messages=[{"role": "user", "content": chunk}],
            max_tokens=512
        )
        results.append(response.choices[0].message.content)
    return "\n".join(results)
```

### 限制 3：无法直接执行 Bash

**解决方案**：通过 MCP Shell 服务器

```bash
# 安装 MCP Shell
npm install -g @modelcontextprotocol/server-shell

# 配置
cat >> mcp-config.json << 'EOF'
{
  "shell": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-shell"]
  }
}
EOF
```

---

## 故障排查

### 常见问题

| 问题 | 检查方法 | 解决方案 |
|------|---------|---------|
| 连接被拒绝 | `telnet 192.168.1.100 8000` | 确认 `--host 0.0.0.0`，检查防火墙 |
| 认证失败 | 查看服务器日志 | 确认 API Key 一致 |
| 响应慢 | `ping 192.168.1.100` | 使用 5GHz WiFi，减少并发 |
| 模型未加载 | 访问 `/admin` | 在管理页面手动加载 |
| OOM 崩溃 | `memory_pressure` | 降低 `--memory-guard-gb` 上限（或改用 `--memory-guard safe`） |

### 日志位置

```bash
# 服务器日志
tail -f ~/.omlx/logs/server.log

# 启动日志
tail -f ~/.omlx/logs/launchd.out
tail -f ~/.omlx/logs/launchd.err
```

### 性能监控

```bash
# 查看内存使用
ps aux | grep omlx

# 查看缓存统计
cat ~/.omlx/cache/stats.json

# 访问管理面板
open http://192.168.1.100:8000/admin
```

---

## 附录

### A. 完整配置示例

#### 服务器配置 (~/.omlx/settings.json)

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8000,
    "log_level": "info"
  },
  "model": {
    "model_dir": "~/Qwen3.5-35B-A3B-Uncensored-HauhauCS-Aggressive/models/Qwen3.5-35B-A3B-mlx-4bit"
  },
  "memory": {
    "memory_guard_tier": "custom",
    "memory_guard_custom_ceiling_gb": 24
  },
  "cache": {
    "enabled": true,
    "ssd_cache_dir": "~/.omlx/cache",
    "ssd_cache_max_size": "50GB",
    "hot_cache_max_size": "4GB"
  },
  "auth": {
    "api_key": "your-claude-code-key",
    "skip_api_key_verification": true
  }
}
```

#### Claude Code 配置

```json
{
  "model": {
    "provider": "openai-compatible",
    "name": "Qwen3.5-35B-A3B-mlx-4bit",
    "base_url": "http://192.168.1.100:8000/v1",
    "api_key": "your-claude-code-key",
    "context_window": 32768,
    "max_tokens": 4096,
    "temperature": 0.7
  },
  "features": {
    "tool_use": false,
    "bash_execution": false,
    "file_editing": true
  }
}
```

### B. 快速参考卡

```
服务器地址：http://<SERVER_IP>:8000
API 端点：   http://<SERVER_IP>:8000/v1
管理面板：  http://<SERVER_IP>:8000/admin
健康检查：  http://<SERVER_IP>:8000/health

启动命令:
  ./scripts/start_server.sh --model-type 4bit --api-key your-key

客户端测试:
  python scripts/client.py --host <SERVER_IP> --check
```

### C. 相关文档

- [网络部署指南](./NETWORK_DEPLOYMENT.md)
- [omlx README](../README.md)

---

*最后更新：2026-03-17*
