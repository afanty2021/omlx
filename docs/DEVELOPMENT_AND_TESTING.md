# oMLX 开发与测试指南（本机实操）

> 最后更新：2026-08-19
> 适用版本：oMLX v0.6.1
> 定位：记录在本机（Apple Silicon）开发与测试 oMLX 的**实操流程与踩过的坑**。
> 通用贡献流程（Fork / PR / License）见 [CONTRIBUTING.md](CONTRIBUTING.md)；本文档聚焦**本机环境与运行陷阱**。

---

## 0. TL;DR 速查

```bash
# 所有命令都必须在 Quant-3.11 conda 环境下执行（见第 1 节）
PY=/opt/homebrew/Caskroom/miniconda/base/envs/Quant-3.11/bin/python
OMLX=/opt/homebrew/Caskroom/miniconda/base/envs/Quant-3.11/bin/omlx

# 启动服务器（默认 8000 常被占用，建议用 8001）
nohup $OMLX serve --model-dir ~/.omlx/models --host 0.0.0.0 --port 8001 \
  > ~/.omlx/logs/serve_8001.log 2>&1 &

# 健康检查
curl -s http://localhost:8001/health

# 列出已发现模型
curl -s http://localhost:8001/v1/models | python3 -m json.tool

# 跑单元测试
$PY -m pytest -m "not slow and not integration"
```

---

## 1. 运行环境（最重要的坑）

### 1.1 ⚠️ 必须使用 `Quant-3.11` conda 环境

oMLX **不能**用系统 `/opt/homebrew/bin/omlx` 或裸 `python3` 运行。当前代码（v0.6.1）的 `omlx/speculative/vlm_mtp.py` 硬依赖 `mlx_vlm.speculative` 子模块，需要 `mlx-vlm >= 0.6.1`。

| 环境 | python | mlx-vlm | `speculative` | 结果 |
|------|--------|---------|---------------|------|
| 系统 `/opt/homebrew/bin/omlx` | 3.11 | 0.4.x | ❌ 缺失 | **启动崩溃** |
| **`Quant-3.11`** | **3.11.14** | **0.6.1** | ✅ 可用 | **正常** |

**Quant-3.11 环境关键依赖：** python 3.11.14、mlx-vlm 0.6.1、mlx-lm 0.31.3。

### 1.2 验证环境是否就绪

```bash
PY=/opt/homebrew/Caskroom/miniconda/base/envs/Quant-3.11/bin/python
$PY -c "from mlx_vlm.speculative import load_drafter; print('✅ speculative 可用')"
$PY -c "import omlx; print('omlx:', omlx.__file__)"
```

两条都成功才能继续。

### 1.3 ⚠️ 系统 `omlx` CLI 的 editable install 会失效

pip 的 editable install（`__editable___omlx_*_finder.py`）把包路径**硬编码**进 finder 文件。如果项目目录被移动/重命名（例如从 `~/Github/omlx` 移到 `~/Github/AI-Infra/omlx`），CLI 会报 `ModuleNotFoundError: No module named 'omlx'`。

**修复方法**（见第 6 节）。但**本机开发请直接用 Quant-3.11 的 `bin/omlx`**，避免依赖系统的 editable install。

---

## 2. 启动服务器

### 2.1 端口选择

默认端口 **8000 经常被占用**（本机上曾被 CAT/IRT 测评服务、Docker 等占据）。**约定使用 8001** 作为 oMLX 开发端口。

启动前先确认端口空闲：

```bash
lsof -i :8001 -P -n | grep LISTEN   # 无输出 = 空闲
```

### 2.2 启动命令

```bash
OMLX=/opt/homebrew/Caskroom/miniconda/base/envs/Quant-3.11/bin/omlx
mkdir -p ~/.omlx/logs
nohup $OMLX serve \
  --model-dir ~/.omlx/models \
  --host 0.0.0.0 \
  --port 8001 \
  > ~/.omlx/logs/serve_8001.log 2>&1 &
echo "PID=$!"
```

- `--model-dir` 默认 `~/.omlx/models`，可省略
- `--host 0.0.0.0` 与 `~/.omlx/settings.json` 的 `server.host` 保持一致（局域网可访问）
- CLI 参数会**覆盖** `settings.json` 中对应字段，并回写（日志会显示 "Saved CLI arguments to settings.json"）

> 管理命令：`omlx start` / `omlx stop` / `omlx restart` 是通过 macOS app/launcher 管理的后台模式，但**不支持指定端口**。需要自定义端口时用 `omlx serve`。

### 2.3 健康检查与模型验证

```bash
# 健康检查（应返回 {"status":"healthy",...}）
curl -s http://localhost:8001/health

# 已发现的模型列表
curl -s http://localhost:8001/v1/models | python3 -m json.tool
```

启动就绪通常需要 1-5 秒（不加载模型，按需加载）。`engine_pool.loaded_count` 初始为 0 是正常的——模型在首次请求时才加载。

**等待就绪的轮询脚本：**

```bash
for i in $(seq 1 60); do
  curl -s http://localhost:8001/health 2>/dev/null | grep -q healthy && echo "READY after ${i}s" && break
  pgrep -f "omlx serve" >/dev/null || { echo "CRASHED"; break; }
  sleep 1
done
```

### 2.4 手动调用模型验证

```bash
curl -s http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "VibeThinker-3B-fp16",
    "messages": [{"role":"user","content":"1+1=?"}],
    "max_tokens": 256
  }' | python3 -m json.tool
```

> **注意：** 首次请求某模型会触发加载（3B 全精度约 5-10s），响应会延迟。`~/.omlx/settings.json` 中 `auth.api_key=test-key`，但 `skip_api_key_verification=true`，本地调用无需带 key。

---

## 3. 模型管理

### 3.1 模型目录与发现

`--model-dir`（默认 `~/.omlx/models`）下**每个含 `config.json` + `*.safetensors` 的子目录** = 一个 model_id（= 目录名）。

```
~/.omlx/models/
├── VibeThinker-3B-fp16/          → model_id: "VibeThinker-3B-fp16"
│   ├── config.json
│   ├── model-00001-of-00002.safetensors   # 支持 HF 分片格式
│   ├── model-00002-of-00002.safetensors
│   ├── tokenizer.json
│   └── chat_template.jinja
├── gemma-4-26b-a4b-it-4bit/
└── ...
```

**支持 HF 分片格式**（`model-XXXXX-of-YYYYY.safetensors`），无需合并为单文件即可直接加载。

### 3.2 per-model 配置（`~/.omlx/model_settings.json`）

顶层 `models` 字典，**key 必须与目录名完全一致**。每个条目覆盖 `settings.json` 的全局 `sampling` 默认值。

关键字段（源码 `omlx/model_settings.py` 的 `ModelSettings` 类）：

| 字段 | 说明 |
|------|------|
| `max_context_window` / `max_tokens` | 生成上限；深度思考模型需设大（如 32768） |
| `temperature` / `top_p` / `force_sampling` | 采样参数 |
| `ttl_seconds` | 空闲自动卸载秒数（`models` 部分有效；`profiles` 部分会被迁移剥离） |
| `thinking_budget_enabled` | 思维 token 预算（一般 `false`） |
| `turboquant_kv_enabled` + `turboquant_kv_bits` | KV cache 量化；全精度推理设 `false` |
| `dflash_enabled` + `dflash_draft_model` | DFlash 推测解码草稿模型路径 |
| `is_pinned` | pin 在内存，不被 LRU 驱逐 |
| `is_default` | 默认模型 |
| `trust_remote_code` | 非标准架构才设 `true`（Qwen2 等标准架构设 `false`） |

**新增模型的标准条目模板：**

```json
"你的模型目录名": {
  "max_context_window": 131072,
  "max_tokens": 32768,
  "temperature": 0.7,
  "top_p": 0.9,
  "force_sampling": false,
  "ttl_seconds": 1800,
  "thinking_budget_enabled": false,
  "guided_grammar_enabled": false,
  "turboquant_kv_enabled": false,
  "turboquant_kv_bits": 4,
  "turboquant_skip_last": true,
  "specprefill_enabled": false,
  "dflash_enabled": false,
  "dflash_in_memory_cache": true,
  "dflash_in_memory_cache_max_entries": 4,
  "dflash_in_memory_cache_max_bytes": 8589934592,
  "dflash_ssd_cache": false,
  "dflash_ssd_cache_max_bytes": 21474836480,
  "mtp_enabled": false,
  "vlm_mtp_enabled": false,
  "is_pinned": false,
  "is_default": false,
  "trust_remote_code": false
}
```

**修改前务必备份：**

```bash
cp ~/.omlx/model_settings.json ~/.omlx/model_settings.json.backup.$(date +%Y%m%d_%H%M%S)
```

### 3.3 模型转换（MLX 格式）

`mlx-community` 组织发布的多为**量化版**（4bit/8bit）。需要**全精度（BF16）**时自行转换：

```bash
PY=/opt/homebrew/Caskroom/miniconda/base/envs/Quant-3.11/bin/python

# 全精度（不加 --q-bits = 保持 bf16，约等于参数量×2 字节）
$PY -m mlx_lm.convert \
  --hf-path WeiboAI/VibeThinker-3B \
  --mlx-path ~/.omlx/models/VibeThinker-3B-fp16

# 量化版（4bit）
$PY -m mlx_lm.convert \
  --hf-path WeiboAI/VibeThinker-3B \
  --mlx-path ~/.omlx/models/VibeThinker-3B-4bit \
  --q-bits 4
```

- 转换产物直接放进 `--model-dir` 即被自动发现
- 转换用 `mlx-lm`（不是 `mlx_lm.convert` CLI，而是 `python -m mlx_lm.convert`），参数已实测：`--hf-path` / `--mlx-path` / `--q-bits`

### 3.4 ⚠️ mlx_lm sampler API 变化（写测试/脚本必看）

`mlx-lm >= 0.31.2` 的 `generate()` **不再接受** `temp=` / `top_p=` 关键字参数，改用 `sampler` 对象。写推理脚本时会踩坑：

```python
# ❌ 旧 API（会报 generate_step() got an unexpected keyword argument 'temp'）
from mlx_lm import generate
generate(model, tokenizer, prompt=prompt, temp=1.0, top_p=0.95)

# ✅ 新 API（0.31.2+）
from mlx_lm import load, generate
from mlx_lm.sample_utils import make_sampler   # 注意是 sample_utils 不是 sample

sampler = make_sampler(temp=1.0, top_p=0.95)
generate(model, tokenizer, prompt=prompt, max_tokens=4096, sampler=sampler, verbose=False)
```

检查 API 签名：

```bash
$PY -c "import inspect; from mlx_lm.sample_utils import make_sampler; print(inspect.signature(make_sampler))"
```

---

## 4. 测试

### 4.1 单元测试

```bash
PY=/opt/homebrew/Caskroom/miniconda/base/envs/Quant-3.11/bin/python

# 默认（排除 slow 和 integration）——日常开发用这个
$PY -m pytest

# 指定文件
$PY -m pytest tests/test_model_discovery.py -v

# 包含慢速测试（需要加载模型文件）
$PY -m pytest -m slow

# 集成测试（需要运行中的服务器，先按第 2 节启动 oMLX）
$PY -m pytest -m integration
```

**pytest 标记**（定义于 `pytest.ini`）：

| Marker | 说明 |
|--------|------|
| `slow` | 需要加载真实模型 |
| `integration` | 需要运行中的服务器 |
| `turboquant` | TurboQuant KV cache 测试 |

**测试约定：** 源文件 `omlx/<module>.py` → 测试文件 `tests/test_<module>.py`。`pytest.ini` 默认 `addopts = -m "not slow and not integration"`。

`tests/conftest.py` 在导入时会安装 torch stub（`omlx._torch_stub`），以满足 xgrammar 的 import 期 torch 引用——DMG 布局下必需，有真 torch 时为 no-op。

### 4.2 手动 API 验证流程

每次改动 API/适配器后，按此 checklist 走一遍：

```bash
# 1. 服务健康
curl -s http://localhost:8001/health

# 2. 模型已发现
curl -s http://localhost:8001/v1/models | python3 -m json.tool

# 3. chat completion（触发模型加载）
curl -s http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"<model_id>","messages":[{"role":"user","content":"hello"}],"max_tokens":64}' \
  | python3 -m json.tool

# 4. 查看启动/运行日志排错
tail -50 ~/.omlx/logs/serve_8001.log
```

### 4.3 模型能力测评（写自定义 eval 时）

深度思考模型（如 VibeThinker）默认高温采样 + 超长输出，测评脚本要点：

- 设足够大的 `max_tokens`（数学推理常需 3000-4000 tokens 的 `<think>`）
- 计时与 token 吞吐：`tokens / elapsed = tok/s`
- 全精度 BF16 的 3B 模型在本机约 **35 tok/s**（裸 mlx_lm，无推测解码）作参考基线
- 评估**答案正确性**要人工/脚本验证，不要只看关键词命中

---

## 5. 常见错误诊断对照表

| 症状 | 根因 | 解决 |
|------|------|------|
| `ModuleNotFoundError: No module named 'omlx'` | 系统 editable install 指向已移动/删除的目录 | 用 Quant-3.11 的 `bin/omlx`；或按第 6 节修 finder |
| `ModuleNotFoundError: No module named 'mlx_vlm.speculative'` | mlx-vlm 版本太旧（< 0.6.1） | 切换到 Quant-3.11 环境（该环境 mlx-vlm 0.6.1） |
| `generate_step() got an unexpected keyword argument 'temp'` | mlx-lm 0.31.2+ API 变化 | 改用 `make_sampler(temp=, top_p=)` 传 `sampler=`，见 3.4 |
| 端口 8000 启动失败 / 连上的是别的服务 | 8000 被其他进程占用（Docker/CAT 等） | 用 `--port 8001`；`lsof -i :8000` 排查占用者 |
| `/v1/models` 返回 404 | 端点路径错或服务未完全启动 | 确认 `/health` 先 healthy；正确路径是 `/v1/models` |
| 模型在列表里但请求 404 | 模型名拼写 / 配置 key 与目录名不一致 | `model_settings.json` 的 key 必须**完全等于**目录名 |
| 首次请求很慢（数秒~十几秒） | 模型按需加载，非启动预加载 | 正常现象；要常驻设 `is_pinned: true` |
| `pip install -e` 失败（403/setuptools） | 清华镜像源偶发 403 | 重试 / 换源 / 不重装，直接用 Quant-3.11 已有依赖 |

---

## 6. 修复系统 editable install（可选）

仅当确需用 `/opt/homebrew/bin/omlx`（系统 CLI）时执行。**本机开发优先用 Quant-3.11 的 `bin/omlx`，可跳过本节。**

editable finder 文件路径：

```
/opt/homebrew/lib/python3.11/site-packages/__editable___omlx_0_3_6_finder.py
```

把其中失效的旧项目路径替换为当前路径：

```bash
FINDER=/opt/homebrew/lib/python3.11/site-packages/__editable___omlx_0_3_6_finder.py
cp "$FINDER" "$FINDER.bak"
sed -i '' 's|/Users/berton/Github/omlx|/Users/berton/Github/AI-Infra/omlx|g' "$FINDER"
rm -f /opt/homebrew/lib/python3.11/site-packages/__pycache__/__editable___omlx_0_3_6_finder.cpython-311.pyc
omlx --help   # 验证
```

> 更彻底的修复是 `pip install -e ".[dev]"`（在 `AI-Infra/omlx` 目录下），但本机镜像源不稳定时可能失败。

---

## 相关文档

- [CONTRIBUTING.md](CONTRIBUTING.md) — 通用贡献流程（Fork / PR / License / 代码风格）
- [CLAUDE_CODE_INTEGRATION.md](CLAUDE_CODE_INTEGRATION.md) — Claude Code 集成
- [oQ_Quantization.md](oQ_Quantization.md) — oQ / TurboQuant KV 量化
- [NETWORK_DEPLOYMENT.md](NETWORK_DEPLOYMENT.md) — 局域网部署
- 项目根 [CLAUDE.md](../CLAUDE.md) — 项目总览与架构
