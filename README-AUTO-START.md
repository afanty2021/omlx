# OMLX 自动启动配置

> 配置日期：2026-05-09

## 配置概览

OMLX 服务器已配置为 macOS LaunchAgent，会在用户登录时自动启动。

## 配置文件

**LaunchAgent Plist**：`~/Library/LaunchAgents/com.omlx.server.plist`

**关键配置**：
- 服务地址：`http://0.0.0.0:8000`
- 模型目录：`~/.omlx/models`
- Conda 环境：`Quant-3.11`
- 日志文件：`~/.omlx/logs/omlx-server.log`

## 可用模型

- ✅ **UI-TARS-1.5-7B-6bit** - GUI 自动化视觉模型（已配置给 Hermes）
- ✅ **Gemma-4-31B-JANG_4M-CRACK** - 通用大语言模型
- ✅ **gemma-4-26b-a4b-it-4bit** - 辅助模型

## 管理命令

### 使用管理脚本（推荐）

```bash
cd /Users/berton/Github/omlx
./omlx-service.sh {start|stop|restart|status|logs}
```

### 使用 launchctl

```bash
# 查看服务状态
launchctl list | grep com.omlx

# 停止服务
launchctl unload ~/Library/LaunchAgents/com.omlx.server.plist

# 启动服务
launchctl load ~/Library/LaunchAgents/com.omlx.server.plist

# 重启服务
launchctl unload ~/Library/LaunchAgents/com.omlx.server.plist
launchctl load ~/Library/LaunchAgents/com.omlx.server.plist
```

## 验证服务

```bash
# 测试 API 端点
curl http://127.0.0.1:8000/v1/models

# 查看进程
pgrep -f "omlx serve"

# 查看日志
tail -f ~/.omlx/logs/omlx-server.log
```

## 故障排查

### 服务未启动

1. 检查日志：
   ```bash
   cat ~/.omlx/logs/omlx-server-error.log
   ```

2. 手动测试：
   ```bash
   cd /Users/berton/Github/omlx
   ./restart_omlx.sh
   ```

3. 重新加载：
   ```bash
   launchctl unload ~/Library/LaunchAgents/com.omlx.server.plist
   launchctl load ~/Library/LaunchAgents/com.omlx.server.plist
   ```

### 端口被占用

```bash
# 查找占用 8000 端口的进程
lsof -i :8000

# 停止进程
kill -9 <PID>
```

## Hermes 配置

OMLX 已配置为 Hermes 的视觉模型提供者：

```yaml
auxiliary:
  vision:
    api_key: siRfoz-giffab-muqko4
    base_url: http://127.0.0.1:8000/v1
    model: UI-TARS-1.5-7B-6bit
    provider: omlx
```

## 相关文件

- LaunchAgent 配置：`~/Library/LaunchAgents/com.omlx.server.plist`
- 管理脚本：`/Users/berton/Github/omlx/omlx-service.sh`
- 重启脚本：`/Users/berton/Github/omlx/restart_omlx.sh`
- 服务日志：`~/.omlx/logs/omlx-server.log`
- 错误日志：`~/.omlx/logs/omlx-server-error.log`

## 注意事项

⚠️ **KeepAlive 配置**：服务会在崩溃时自动重启，但不会在正常退出后重启（SuccessfulExit: false）

⚠️ **进程优先级**：Nice 值为 10，降低了优先级以避免影响系统性能

⚠️ **文件句柄限制**：设置为 10240，以支持多模型并发服务

---

*配置完成于 2026-05-09 by Claude Code*
