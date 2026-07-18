---
name: ml-web-course-project-wsl
description: Blueprint for building full-stack ML web app course projects (BERT + Flask + Vue) in WSL — handles /mnt/ mount restrictions, spec-driven development, model training, and course documentation.
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [wsl, course-project, flask, bert, vue, ml-web-app, nlp]
    related_skills: [writing-plans, subagent-driven-development, docx]
---

# ML Web Course Project — WSL Blueprint

## Overview

When building a full-stack ML web application course project (BERT model + Flask API + Vue frontend) inside WSL, the `/mnt/` mount (Windows drive) has **two critical limitations**:

1. **npm install** fails with EPERM on chmod — node_modules packages need permission changes that WSL's 9P protocol doesn't support on mounted Windows drives.
2. **uv sync / pip install** fails with "Operation not permitted" when copying `.so` files into `.venv` under `/mnt/`.

**Solution:** Dual-directory pattern — develop in WSL home (`~/`), deliver in `/mnt/`.

## When to Use

**Trigger conditions — load this skill when ALL of the following are true:**

- User is working in WSL (Windows Subsystem for Linux)
- Building a course/academic project with Python ML models (PyTorch, transformers, etc.)
- Using Flask (or similar) as web backend
- Using Vue / React / any npm-based frontend
- Project deliverables need to live on a Windows drive (/mnt/c/, /mnt/d/, /mnt/e/, etc.)
- Need to generate course documentation (specification, architecture, experiment results)

**Also trigger when:**
- User says "npm install fails with EPERM on /mnt/"
- User says "uv sync fails with operation not permitted"
- User mentions "course project" + "NLP" + "Flask" together

## WSL Dual-Directory Pattern

### Overview

```
~/project/              ← Development environment (WSL native filesystem)
    .venv/              ← uv sync works here
    node_modules/       ← npm install works here
    model/
    backend/
    frontend/
    .spec/              ← Spec-kit artifacts

/mnt/e/ToDo/.../        ← Deliverable source (Windows drive)
    model/
    backend/
    frontend/src/       ← Source files only (no node_modules or .venv)
    docs/
    .spec/
```

### Step-by-step

**Step 1: Create dev directory in WSL home**

```bash
mkdir -p ~/nlp-sentiment
cp -r "/mnt/e/ToDo/University-Natural Language Processin/model" ~/nlp-sentiment/
cp -r "/mnt/e/ToDo/University-Natural Language Processin/backend" ~/nlp-sentiment/
cp "/mnt/e/ToDo/University-Natural Language Processin/pyproject.toml" ~/nlp-sentiment/
```

**Step 2: Install Python dependencies (works on ~/)**

```bash
cd ~/nlp-sentiment && uv sync
# If proxy issues:
#   unset ALL_PROXY http_proxy https_proxy
#   uv sync
```

**Step 3: Install frontend dependencies (works on ~/)**

```bash
cd ~/nlp-sentiment && npm init vite frontend -- --template vue
cd frontend && npm install
```

**Step 4: Write source files to /mnt/ first (deliverable)**

The deliverable directory on Windows is the canonical source of truth for code files (`.vue`, `.py`, `.md`). Write files there using tools like `write_file`.

**Step 5: Sync source to development directory**

```bash
# Copy Python/model files
cp -r "/mnt/e/.../model/" ~/nlp-sentiment/
cp -r "/mnt/e/.../backend/" ~/nlp-sentiment/

# Copy frontend source files only (exclude node_modules)
cp "/mnt/e/.../frontend/src/"* ~/nlp-sentiment/frontend/src/ -r
cp "/mnt/e/.../frontend/vite.config.js" ~/nlp-sentiment/frontend/
cp "/mnt/e/.../frontend/index.html" ~/nlp-sentiment/frontend/
cp "/mnt/e/.../frontend/package.json" ~/nlp-sentiment/frontend/
```

**Step 6: Run in dev directory**

```bash
# Backend
cd ~/nlp-sentiment && .venv/bin/python backend/app.py

# Frontend (separate terminal)
cd ~/nlp-sentiment/frontend && npm run dev
```

## Spec-Driven Development (Spec-Kit Adaptation)

When `specify init` fails on `/mnt/` due to permissions, manually create the spec structure:

```bash
mkdir -p .spec
```

Create these files manually:

### `.spec/constitution.md`

Project governing principles, tech stack constraints, and acceptance criteria.

### `.spec/specification.md`

User stories and functional specs (F1, F2, F3...). What to build, not how.

### `.spec/plan.md`

Architecture diagram, directory structure, tech stack rationale, API design, data flow.

### `.spec/tasks.md`

Break implementation into phases:
- Phase 1: Environment setup
- Phase 2: Model training
- Phase 3: Backend API
- Phase 4: Frontend
- Phase 5: Documentation
- Phase 6: Git + delivery

## Course Project Structure (BERT + Flask + Vue)

```
project/
├── .spec/                    # Spec-kit artifacts
│   ├── constitution.md
│   ├── specification.md
│   ├── plan.md
│   └── tasks.md
├── model/
│   ├── config.py             # Training config
│   ├── dataset.py            # HuggingFace dataset loading + tokenization
│   ├── model.py              # BERT model creation
│   ├── train.py              # Trainer-based fine-tuning
│   └── inference.py          # Predictor class for Flask
├── backend/
│   ├── config.py             # Flask config
│   ├── predictor.py          # Model wrapper for Flask routes
│   └── app.py                # Flask entry point with REST API
├── frontend/
│   ├── src/
│   │   ├── api/sentiment.js  # API layer (fetch wrappers)
│   │   ├── components/
│   │   │   ├── AnalysisForm.vue
│   │   │   ├── ResultDisplay.vue
│   │   │   ├── SentimentGauge.vue  # Canvas-based gauge
│   │   │   ├── BatchUpload.vue
│   │   │   └── ModelInfo.vue
│   │   └── App.vue
│   ├── index.html
│   ├── vite.config.js        # Proxy /api -> localhost:5000
│   └── package.json
├── docs/
│   └── 课程设计报告.md
├── pyproject.toml
└── README.md
```

## Flask API Template

Minimal Flask app with three endpoints:

```python
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd

app = Flask(__name__)
CORS(app)  # Vue dev server needs CORS

@app.route("/api/predict", methods=["POST"])
def predict():
    data = request.get_json()
    text = data["text"].strip()
    if not text:
        return jsonify({"error": "文本不能为空"}), 400
    result = predictor.predict(text)
    return jsonify(result)

@app.route("/api/predict/batch", methods=["POST"])
def predict_batch():
    file = request.files["file"]
    df = pd.read_csv(file)
    # Auto-detect text column
    # Predict each row
    # Return CSV with results

@app.route("/api/model/info", methods=["GET"])
def model_info():
    return jsonify({
        "model": "bert-base-chinese",
        "dataset": "...",
        "framework": "PyTorch + Transformers",
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

## Vue Frontend Key Patterns

### vite.config.js — proxy setup

```js
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: { '/api': { target: 'http://localhost:5000', changeOrigin: true } },
  },
})
```

### API layer — fetch wrappers

```js
export async function predictSentiment(text) {
  const res = await fetch('/api/predict', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
  if (!res.ok) throw new Error((await res.json()).error)
  return res.json()
}
```

### Canvas Gauge Component

Use Canvas 2D to draw a semi-circular gauge:
- Background arc (180°)
- Filled arc (proportional to confidence)
- Center text: percentage
- Color: green/red based on positive/negative

## Course Documentation Template

The report (`docs/课程设计报告.md`) should cover:
1. 选题背景与意义
2. 系统架构
3. 模型设计与训练（BERT 简介、数据集、微调方法、实验结果）
4. Web 系统实现（后端 API + 前端组件 + 部署方式）
5. 核心代码分析
6. 总结与展望
7. 参考文献

## Common Pitfalls

### 1. Proxy blocks HuggingFace download

WSL often has proxy env vars set (`ALL_PROXY`, `http_proxy`). HuggingFace datasets hub may fail with SSL errors or SOCKS proxy issues.

**Fix:** Three solutions (try in order):

**a) Use Chinese HuggingFace mirror (fastest, no proxy unset needed):**
```bash
env HF_ENDPOINT=https://hf-mirror.com .venv/bin/python model/train.py
```
The mirror is accessible through most proxy setups and is faster for Chinese networks.

**IMPORTANT:** The `datasets` library does NOT respect `HF_ENDPOINT` for dataset downloads — only `huggingface_hub` model downloads use it. If dataset download fails, use a local CSV fallback (see pitfall 2).

**b) Unset proxies:**
```bash
unset ALL_PROXY http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
.venv/bin/python model/train.py
```
If the environment needs the proxy for general internet, use `env -u`:
```bash
env -u http_proxy -u https_proxy -u ALL_PROXY -u HTTP_PROXY -u HTTPS_PROXY .venv/bin/python model/train.py
```

**c) Install socksio (if SOCKS proxy error):**
```bash
uv add socksio
```

**d) Download model weights directly via mirror + curl:**
```bash
env HF_ENDPOINT=https://hf-mirror.com curl -L -o ~/.cache/huggingface/hub/models--bert-base-chinese/blobs/pytorch_model.bin \
  "https://hf-mirror.com/google-bert/bert-base-chinese/resolve/main/pytorch_model.bin"
```

### 2. Dataset download failures

HuggingFace datasets (WeiboSenti100k, ChnSentiCorp) may fail to download through WSL proxies.

**Fix:** Use a local CSV dataset from GitHub as fallback:

| Dataset | Source | Size | Format |
|---------|--------|------|--------|
| waimai_10k | `SophonPlus/ChineseNlpCorpus` | 12k rows | `label,review` (0/1, Chinese) |
| online_shopping_10_cats | HuggingFace: `seamew/ChnSentiCorp` | 24k rows | Hotel reviews |

```bash
# Download waimai_10k as fallback
env http_proxy=http://127.0.0.1:7890 curl -L -o model/data/waimai.csv \
  "https://raw.githubusercontent.com/SophonPlus/ChineseNlpCorpus/master/datasets/waimai_10k/waimai_10k.csv"
```

**Modify `dataset.py` to load from local CSV:**
```python
import pandas as pd
from sklearn.model_selection import train_test_split

df = pd.read_csv("model/data/waimai.csv")
df = df.rename(columns={"review": "text", "label": "label"})
train_df, test_df = train_test_split(df, test_size=0.1, random_state=42)
train_dataset = Dataset.from_pandas(train_df[["text", "label"]])
eval_dataset = Dataset.from_pandas(test_df[["text", "label"]])
```

### 3. npm creates .vscode that conflicts

`npm create vite` scaffolds a `.vscode/` directory. If your project root already has one, the scaffold may fail. Either remove existing `.vscode` first, or scaffold in `/tmp/` and copy.

### 4. Background processes lose stdout in Hermes WSL

Hermes `terminal(background=true)` may fail to capture stdout for some processes (especially Vite dev servers), returning 502 when the server is actually running but the output is not captured.

**Vite 6 dev server in background:** Produces 502 when run via `terminal(background=true)`. Build output works correctly. Workaround: build first, then preview:

```bash
# Instead of npm run dev in background:
npm run build
npx vite preview
```

Alternative for builds that the terminal tool rejects as "long-lived server":
```bash
# Use node execSync wrapper (build.sh):
echo 'node -e "const{execSync}=require(\"child_process\");console.log(execSync(\"npx vite build\",{encoding:\"utf8\",timeout:120000}))"' > build.sh
bash build.sh
```

### 5. `backend/config.py` 与 `model/config.py` 同名冲突

当 Flask 后端和模型模块都有 `config.py` 时，Python 模块缓存会导致一个遮蔽另一个：
- `app.py` 先 `from config import BACKEND_CONFIG` → Python 缓存了 `backend/config.py`
- `predictor.py` 把 `model/` 加到 `sys.path[0]`
- `inference.py` 执行 `from config import SAVED_MODEL_DIR` → Python 从缓存返回 `backend/config.py`（不是 `model/config.py`），导入失败

**Fix:** 重命名其中一个避免冲突：
```bash
mv backend/config.py backend/backend_config.py
```
然后在 `app.py` 中：
```python
# 必须在 predictor import 之前
from backend_config import BACKEND_CONFIG
from predictor import predict, predict_batch, get_model_info
```

### 6. `return_all_scores=True` pipeline 输出格式陷阱

`pipeline(..., return_all_scores=True)` 返回的是**列表**，不是带 `scores` key 的单字典：

```python
# ✓ 实际格式
result = pipe(text)
# result = [
#   {'label': 'LABEL_0', 'score': 0.979},
#   {'label': 'LABEL_1', 'score': 0.021},
# ]

# ✗ 错误读取（会得到 None，回退到 1-score 逻辑，概率对调）
scores = result[0].get("scores", None)  # ← None!
```

**正确做法：遍历列表按 label 提取：**
```python
neg_score = pos_score = 0.0
for r in result:
    if r["label"] in ("LABEL_0", "负面"):
        neg_score = r["score"]
    elif r["label"] in ("LABEL_1", "正面"):
        pos_score = r["score"]
# 回退：如果 pipeline 没返回完整列表
if neg_score == 0.0 and pos_score == 0.0:
    if pred_label == "正面":
        pos_score = confidence; neg_score = 1 - confidence
    else:
        neg_score = confidence; pos_score = 1 - confidence
```

### 7. Flask 后端在 Hermes background mode 下的启动方式

`terminal(background=true)` 在 Hermes 中可能不会正确启动 Python 进程（表现为进程显示 running 但无输出、端口未监听）。**可靠方式**是用 `execute_code` + `subprocess.Popen`：

```python
import subprocess, os
log_file = "/tmp/flask_backend.log"
with open(log_file, "w") as f:
    proc = subprocess.Popen(
        ["path/to/.venv/bin/python", "path/to/backend/app.py"],
        stdout=f, stderr=subprocess.STDOUT,
        cwd="path/to/project",
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
    )
# 等待就绪
for i in range(15):
    import time, urllib.request, json
    time.sleep(1)
    try:
        resp = urllib.request.urlopen("http://127.0.0.1:5000/api/health", timeout=2)
        print(f"Backend ready after {i+1}s")
        break
    except: pass
```

### 8. Transformers 5.x API migration (vs 4.x)

When writing training code with HuggingFace `transformers >= 5.0`, these APIs changed from 4.x:

| 4.x (old) | 5.x (new) | Notes |
|-----------|-----------|-------|
| `Trainer(tokenizer=...)` | `Trainer(processing_class=...)` | `tokenizer` kwarg removed |
| `TrainingArguments(evaluation_strategy=...)` | `TrainingArguments(eval_strategy=...)` | Renamed |
| `TrainingArguments(logging_dir=...)` | Use env var `TENSORBOARD_LOGGING_DIR` | Parameter removed |
| Model saves as `pytorch_model.bin` | Model saves as `model.safetensors` | Default format changed |
| `pipeline()` returns `{"label":"LABEL_0/1"}` | May return `{"label":"正面/负面"}` | Depends on model config's `id2label` |
| `pipeline()` always has `scores` key | `scores` key may be absent | Must handle both cases |

**Inference wrapper must handle both pipeline output formats:**

When `return_all_scores=True`, pipeline returns a list of dicts, one per class label:

```python
# ✓ Correct: iterate over result list
result = pipe(text)  # [{'label':'LABEL_0','score':x}, {'label':'LABEL_1','score':y}]
label_map = {"正面": "正面", "负面": "负面", "LABEL_0": "负面", "LABEL_1": "正面"}
pred_label = label_map.get(result[0]["label"], result[0]["label"])

neg_score = pos_score = 0.0
for r in result:
    if r["label"] in ("LABEL_0", "负面"):
        neg_score = r["score"]
    elif r["label"] in ("LABEL_1", "正面"):
        pos_score = r["score"]
if neg_score == 0.0 and pos_score == 0.0:
    # Fallback: single-result pipeline (no return_all_scores)
    if pred_label == "正面":
        pos_score, neg_score = result[0]["score"], 1 - result[0]["score"]
    else:
        neg_score, pos_score = result[0]["score"], 1 - result[0]["score"]
```

Also note: `Trainer.save_model()` now saves safetensors format (`model.safetensors`) instead of `pytorch_model.bin`. Loading with `AutoModelForSequenceClassification.from_pretrained()` handles both transparently.

### 9. Git ownership error on /mnt/

```bash
# Fix: "detected dubious ownership in repository"
git config --global --add safe.directory '/mnt/e/ToDo/University-Natural Language Processin'
```

**Mitigation:** Check training progress via side-channel:
```bash
# Check if model cache is being populated
ls ~/.cache/huggingface/hub/models--bert-base-chinese/blobs/

# Check if saved_model directory is being written
ls -la ~/nlp-sentiment/model/saved_model/

# Monitor GPU usage
nvidia-smi
```

## Verification

After setup, verify:

- [ ] Backend starts: `curl http://localhost:5000/api/health`
- [ ] Frontend compiles: `npm run build` produces no errors
- [ ] Single prediction: `curl -X POST http://localhost:5000/api/predict -H "Content-Type: application/json" -d '{"text":"测试文本"}'`
- [ ] Batch prediction works with CSV upload
- [ ] Vue proxy forwards `/api/*` to backend
- [ ] Model achieves >90% accuracy on test set
