# omlx 局域网部署指南

> 在 Apple Silicon Mac 上部署 omlx 推理服务，通过局域网提供 OpenAI 兼容 API

本文档介绍如何在 Mac 服务器上部署 omlx 框架，并允许局域网内其他设备调用量化模型（4bit/8bit）。

---

## 📋 目录

1. [架构概览](#架构概览)
2. [服务器端配置](#服务器端配置)
3. [客户端调用](#客户端调用)
4. [性能优化](#性能优化)
5. [安全配置](#安全配置)
6. [故障排查](#故障排查)

---

## 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                    局域网部署架构                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐      ┌──────────────┐                     │
│  │  Mac 服务器   │      │  量化模型     │                     │
│  │  omlx serve  │◄────►│  4bit/8bit   │                     │
│  │  192.168.1.100│      │  Qwen3.5     │                     │
│  └──────┬───────┘      └──────────────┘                     │
│         │ 端口：8000                                        │
│         ▼                                                   │
│    ┌────┴────┐    ┌────┴────┐    ┌────┴────┐               │
│    │ 客户端 1 │    │ 客户端 2 │    │ 客户端 3 │               │
│    │ Windows │    │  Linux   │    │  macOS  │               │
│    └─────────┘    └─────────┘    └─────────┘               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 服务器端配置

### 1. 环境要求

| 项目 | 要求 |
|------|------|
| 操作系统 | macOS 15.0+ (Sequoia) |
| 硬件 | Apple Silicon (M1/M2/M3/M4) |
| 内存 | 16GB+ (推荐 32GB+) |
| Python | 3.11–3.13 |
| 模型 | MLX 格式量化模型 |

### 2. 获取本机 IP 地址

```bash
# macOS 获取局域网 IP
ipconfig getifaddr en0

# 或查看详细网络信息
ifconfig | grep "inet " | grep -v 127.0.0.1
```

**输出示例：**
```
inet 192.168.1.100 netmask 0xffffff00 broadcast 192.168.1.255
```

记下 IP 地址（如 `192.168.1.100`），后续客户端需要使用。

### 3. 启动 omlx 服务器

#### 基础配置

```bash
omlx serve \
  --model-dir ~/models \
  --host 0.0.0.0 \
  --port 8000 \
  --api-key your-secret-key-123
```

#### 完整配置（推荐）

```bash
omlx serve \
  --model-dir ~/Qwen3.5-35B-A3B-Uncensored-HauhauCS-Aggressive/models \
  --host 0.0.0.0 \
  --port 8000 \
  --api-key your-secret-key-123 \
  --memory-guard-gb 32 \
  --paged-ssd-cache-dir ~/.omlx/cache \
  --paged-ssd-cache-max-size 50GB \
  --hot-cache-max-size 4GB \
  --log-level info
```

#### 配置参数说明

| 参数 | 说明 | 推荐值 |
|------|------|--------|
| `--host` | 绑定地址，`0.0.0.0` 允许所有网络接口 | `0.0.0.0` |
| `--port` | 服务端口 | `8000` |
| `--api-key` | API 认证密钥 | 自定义强密码 |
| `--memory-guard-gb` | 自定义内存保护上限（GB） | 4bit: 24GB, 8bit: 40GB |
| `--paged-ssd-cache-dir` | SSD 缓存目录 | `~/.omlx/cache` |
| `--hot-cache-max-size` | 内存热缓存大小 | `4GB` |

### 4. 防火墙配置

```bash
# 查看防火墙状态
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate

# 允许 Python 访问
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /opt/homebrew/bin/python3
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblockapp /opt/homebrew/bin/python3

# 或者临时关闭防火墙（仅测试用）
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate off
```

### 5. 验证服务启动

```bash
# 检查端口监听
lsof -i :8000

# 本地测试
curl http://localhost:8000/health

# 预期输出：{"status":"healthy", ...}（启动预加载期间返回 503 与 "loading"）
```

---

## 客户端调用

### 1. Python (OpenAI 兼容)

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://192.168.1.100:8000/v1",
    api_key="your-secret-key-123"
)

response = client.chat.completions.create(
    model="Qwen3.5-35B-A3B-mlx-4bit",
    messages=[{"role": "user", "content": "你好"}],
    max_tokens=512,
    stream=True
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

### 2. Python (Anthropic 兼容)

```python
import anthropic

client = anthropic.Anthropic(
    base_url="http://192.168.1.100:8000/v1",
    api_key="your-secret-key-123"
)

response = client.messages.create(
    model="Qwen3.5-35B-A3B-mlx-4bit",
    max_tokens=512,
    messages=[{"role": "user", "content": "你好"}]
)

print(response.content[0].text)
```

### 3. curl 命令

```bash
# OpenAI 格式
curl -X POST "http://192.168.1.100:8000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-secret-key-123" \
  -d '{
    "model": "Qwen3.5-35B-A3B-mlx-4bit",
    "messages": [{"role": "user", "content": "你好"}],
    "stream": true
  }'
```

### 4. 集成到 AI 工具

#### OpenCode / Claude Code 配置

```json
{
  "providers": {
    "omlx": {
      "base_url": "http://192.168.1.100:8000/v1",
      "api_key": "your-secret-key-123",
      "models": ["Qwen3.5-35B-A3B-mlx-4bit"]
    }
  }
}
```

#### VSCode Continue 配置

```json
{
  "models": [
    {
      "title": "omlx Qwen3.5",
      "provider": "openai",
      "model": "Qwen3.5-35B-A3B-mlx-4bit",
      "apiBase": "http://192.168.1.100:8000/v1",
      "apiKey": "your-secret-key-123"
    }
  ]
}
```

---

## 性能优化

### 1. 网络优化

```bash
# 检查网络延迟
ping -c 10 192.168.1.100

# 测试带宽（服务器端）
brew install iperf3
iperf3 -s

# 测试带宽（客户端）
iperf3 -c 192.168.1.100
```

### 2. 模型配置优化

| 量化版本 | memory-guard-gb | max-concurrent-requests | 预期速度 |
|---------|-----------------|-------------------------|---------|
| 4bit | 24GB | 32 | 70-80 tok/s |
| 8bit | 40GB | 24 | 40-55 tok/s |
| Full | 64GB | 16 | 20-30 tok/s |

### 3. 并发优化

在 `~/.omlx/settings.json` 中配置：

```json
{
  "scheduler": {
    "max_concurrent_requests": 256
  },
  "cache": {
    "enabled": true,
    "ssd_cache_dir": "~/.omlx/cache",
    "ssd_cache_max_size": "50GB",
    "hot_cache_max_size": "4GB"
  }
}
```

### 4. 监控性能

```bash
# 访问管理面板
open http://192.168.1.100:8000/admin

# 查看实时日志
tail -f ~/.omlx/logs/server.log

# 监控内存
watch -n 1 "ps aux | grep omlx | grep -v grep"
```

---

## 安全配置

### 1. 生成安全 API Key

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# 输出示例：Kx8j2Lp9Qm3Nv5Rz7Wy1Ab4Cd6Ef0Gh2
```

### 2. 环境变量管理

```bash
# ~/.zshrc 或 ~/.bashrc
export OMLX_API_KEY="your-secret-key-123"
export OMLX_HOST="192.168.1.100"
export OMLX_PORT="8000"
```

### 3. 限制访问 IP

在路由器配置 ACL，或创建 `/etc/pf.conf` 规则：

```
block in quick on en0 from any to any port 8000
pass in quick on en0 from 192.168.1.0/24 to any port 8000
```

### 4. HTTPS 反向代理（可选）

使用 Caddy：

```caddyfile
https://omlx.your-domain.com {
    reverse_proxy localhost:8000
    tls your-email@example.com
}
```

---

## 故障排查

### 常见问题解决

| 问题 | 检查方法 | 解决方案 |
|------|---------|---------|
| 连接被拒绝 | `telnet 192.168.1.100 8000` | 确认 `--host 0.0.0.0`，检查防火墙 |
| 认证失败 | 查看服务器日志 | 确认 API Key 一致，检查 Header 格式 |
| 响应慢 | `ping 192.168.1.100` | 使用 5GHz WiFi，减少并发请求 |
| 模型未加载 | 访问 `/admin` | 在管理页面手动加载，检查内存 |
| UTF-8 乱码 | 检查客户端编码 | 确保客户端设置 UTF-8 |

### 日志位置

```bash
# 服务器日志
~/.omlx/logs/server.log

# 启动日志（systemd/launchd）
/tmp/omlx.out
/tmp/omlx.err

# 缓存统计
~/.omlx/cache/stats.json
```

### 健康检查端点

```bash
# 基础健康检查
curl http://192.168.1.100:8000/health

# 模型状态
curl http://192.168.1.100:8000/v1/models
```

---

## 附录

### A. 完整脚本列表

| 文件名 | 用途 |
|--------|------|
| `scripts/start_server.sh` | 服务器启动脚本 |
| `scripts/client.py` | Python 客户端示例 |
| `scripts/test_connection.sh` | 连接测试脚本 |
| `config/omlx-settings.json` | omlx 配置文件 |
| `config/launchd.plist` | macOS 自动启动配置 |

### B. 快速参考卡

```
服务器地址：http://<SERVER_IP>:8000
API 端点：   http://<SERVER_IP>:8000/v1
管理面板：  http://<SERVER_IP>:8000/admin
健康检查：  http://<SERVER_IP>:8000/health
```

---

## 相关文档

- [omlx README](../README.md)

---

*最后更新：2026-08-19*
