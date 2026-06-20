---
name: university-aiagent-course
description: AI Agent开发实战课程作业工作流 — 教材配套代码目录、学生信息替换、作业文件规范、常见坑和修复
---

# AI Agent 开发实战 课程作业

> 大学「Linux 应用程序开发」课程 · 学生：冯周杰(20250421042)

## 项目布局

```
E:\ToDo\University - Linux Applications\  (/mnt/e/ToDo/University - Linux Applications/)
├── assignments/           ← 已完成的作业（编号文件）
│   ├── 0-deepseek_api.py
│   ├── 1-deepseek_api_functioncalling.py
│   ├── 2-agent_react.py
│   ├── 3-llamacpp.py
│   ├── 4-llamafactory.py
│   ├── 5-medical-finetune.md
│   ├── 6-env-setup.py
│   ├── 7-mcp-experiment/  ← MCP Server 实验 (server.py + client)
│   └── 8-mcp-protocols/   ← 三种传输协议 (test_all.py)
├── reference/AIAgent-main/  ← 教材配套代码（第1/2/4/6/7章）
├── mcp-protocols/            ← 老师附件代码（三种MCP协议）
├── materials/                ← 教材材料(思维导图/彩图)
└── pyproject.toml            ← managed=false, venv 软链接到 Linux 侧
```

## 作业处理流程

### 1. 收到新作业

1. **确定章节**：从用户消息找到对应教材章节（如 "4.2-4.3"、"104-105页"）
2. **查参考代码**：先看 `reference/AIAgent-main/第X章/` 有没有配套代码
3. **理解需求**：确认是要跑代码、写方案还是验证环境
4. **替换学生信息**：所有出现「张三」「李四」的地方替换为「冯周杰(20250421042)」

### 2. 学生信息

- 姓名：冯周杰
- 学号：20250421042
- 替换规则：`张三 → 冯周杰(20250421042)`，李四可保留做对比

### 3. 文件规范

- **有代码的作业**：创建 `assignments/N-name.py`（自包含单文件，或子目录）
- **方案文档**：`assignments/N-name.md`
- **老师附件代码**：放在项目根目录下的独立子目录（如 `mcp-protocols/`）
- **每次运行结果必须截图**，输出中要看到学号和姓名

## 环境注意事项

### WSL / NTFS

- WSL 是 Arch Linux，用 `pacman` 不是 `apt`
- **NTFS 盘 (E:) 上 Python venv 有权限问题**：`uv sync`/`pip install` 写入失败
- **解决方案**：venv 建在 Linux 侧 (`~/.venvs/deepseek-api`)，项目目录用 `ln -sf` 软链接 `.venv`
- `pyproject.toml` 设置 `[tool.uv] managed = false` 让 uv 不自动管理 venv
- 所有 Python 命令从 WSL 终端运行，不用 Windows 侧 `uv run`

### 代理

```bash
export HTTP_PROXY=http://127.0.0.1:7890 HTTPS_PROXY=http://127.0.0.1:7890
```

### 模型下载

- HuggingFace 下载容易断 → 优先用 ModelScope（国内 CDN）
- `urllib.request.urlretrieve(url, path)` 比 curl 稳定

## 常见坑
### DeepSeek ReAct Agent (第1章 1.4)

- DeepSeek 不遵守 `PAUSE` 停止指令 → 加 `stop=["PAUSE"]` 参数
- 模型可能用中文冒号 `：` → 正则用 `[:：]` 兼容中英文
- ReAct prompt 模板需包含明确的 Action / Action Input / Observation / Final Answer 标记

#### ReAct 正则兼容

```python
re.search(r"Action[:：]\s*(\w+)", text)
re.search(r"Action Input[:：]\s*({.*?})", text, re.DOTALL)
re.search(r"Final Answer[:：]\s*(.*)", text)
```

### llama.cpp (第4周)
- 新版 llama.cpp 只有 CMake 构建，Makefile 已废弃
- 编译：`cmake -B build -DGGML_CUDA=OFF && cmake --build build --target llama-cli`
- `-st` (single-turn) 标志防止进入交互模式卡住

### LLaMA-Factory (第5周)
- 需要 Python 3.12，用 `uv python install 3.12` 安装
- 先装 PyTorch CPU：`uv pip install torch --index-url https://download.pytorch.org/whl/cpu`
- 再装依赖：`uv pip install transformers datasets...` 然后 `uv pip install -e . --no-deps`

### MCP Server (第8-9周)
- `FastMCP.run()` 只接受 `transport` 参数，不接受 `host/port`
- SSE 服务器：`app = mcp.sse_app(); uvicorn.run(app, host=..., port=...)`
- Streamable：`app = mcp.streamable_http_app(); uvicorn.run(app, host=..., port=...)`
- Stdio 客户端用 subprocess 启动服务器进程，测试完 kill

### 版本信息
- Node.js: v25.2.1 (Windows), v26.2.0 (WSL)
- PostgreSQL: 18.4 (Windows)
- VSCode: Windows 侧，`code` 命令在 WSL 需配置
- Python: 3.13.11 (主 venv), 3.12.12 (LLaMA-Factory)
