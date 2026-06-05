---
name: coursework-organization
description: "Organize university coursework chapter exercises — extract archives, set up code/data structure, fix textbook code, manage dependencies, package for submission."
version: 1.0.0
author: Hermes Agent
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [coursework, university, textbook, chapter-setup, archive-extraction, submission]
---

# Coursework Organization

Use this skill when the user needs to set up, organize, or package textbook chapter exercises for a university course project.

## Trigger conditions

Load this skill when:
- User is working on a textbook chapter and needs `code/` + `data/` structure
- User needs to extract code/data from archives (RAR, ZIP, etc.)
- User wants to package coursework for submission
- User references "章节" (chapter), "课程设计" (course design), or "交作业" (submit assignment)

## Workflow

### 1. Inspect first — never act without understanding

Always start with read-only inspection:
- List the project root (`ls -la`, `find` for structure)
- Check existing chapter patterns (how are previous chapters structured?)
- Read README, pyproject.toml, and any spec docs to understand the project context
- Present a plan **before** extracting, editing, or installing anything

### 2. Follow existing patterns

Each chapter directory should mirror what's already established:
```
第X章/
├── code/
│   └── chapter_X.py          # Single file containing all code blocks
└── data/
    └── (data files needed by the code)
```

- Do NOT include PPT, RAR/ZIP archives, or extra PDFs in the chapter directory
- Do NOT nest content — flatten extracted archives one level up
- Reference materials (PPTs, PDFs) remain in the textbook resource folder

### 3. Extract archives properly

Prefer `7z` over `unrar` (more widely available):
```bash
7z x "第X章/文件.rar" -o"第X章" -y
```

After extraction, flatten nested directories:
```bash
# If RAR produces 第X章/第X章/code/... move content up
cp -r 第X章/第X章/code/ 第X章/code/
cp -r 第X章/第X章/data/ 第X章/data/
rm -rf 第X章/第X章/
```

### 4. Fix common textbook code issues

Chinese NLP textbook code frequently has:
- **Missing quotes** on string/file paths (e.g. `file_path = ../data/file.csv'` → missing opening `'`)
- **Hardcoded Windows fonts** (`C:\\Windows\\Fonts\\simsun`) — OK if running on Windows
- **Excessive DPI** in matplotlib (`dpi=600` → reduce to `dpi=100-120` for screen viewing)
- **Overly large figure sizes** (`figsize=(10, 6)` → reduce height if content is small)
- **Scattered imports** — each code block re-imports modules; this is normal for textbook code, leave as-is

#### 4a. Matplotlib DPI for screens

Textbook code often uses `dpi=600` (print quality), producing a 6000×3600 px window. Fix:

```python
plt.figure(figsize=(10, 5), dpi=120)  # 1200×600 px — fits any screen
plt.xticks(rotation=30)               # less aggressive tilt
plt.xlabel('标签', fontsize=12)       # smaller fonts
plt.title('标题', fontsize=14)         # smaller title
```

**Why 120 DPI**: Standard screen DPI is 96-120. 600 DPI is for print. At 600 DPI, a 10×6" figure = 6000×3600 px. At 120 DPI, same figure = 1200×720 px.

See `references/matplotlib-dpi-for-screens.md` for full rationale and examples.

#### 4b. Convert hardcoded data to CSV (common teacher request)

When a teacher asks students to "use your own data", replace inline `train_data = [...]` with CSV loading:

**Before** (hardcoded in Python):
```python
train_data = [("这个手机太差了。", "消极"), ("今天的天气真好。", "积极")]
```

**After** (`data/my_data.csv`):
```csv
text,label
这个手机太差了。,消极
今天的天气真好。,积极
```

**Updated code**:
```python
import pandas as pd
df = pd.read_csv("../data/my_data.csv")
train_texts = df["text"].tolist()
train_labels = df["label"].tolist()
```

**CSV format conventions**: columns `text` and `label` (or `Sentiment`). Always UTF-8 (use `utf-8-sig` BOM for Excel). Minimum 20 samples, cover diverse topics, keep sentences 10-40 chars.

See `references/csv-data-for-submissions.md` for full column conventions, encoding best practices, and data distribution tips.

### 5. Manage dependencies

- Update `pyproject.toml` with any new dependencies the chapter needs
- Group deps by chapter with comments (`# 第X章：xxx`)
- The user runs `uv sync` (or `pip install`) on their target platform

### 6. Package for submission

**Core principle**: A teacher should be able to unzip → run → see results in under 30 seconds. Never submit raw code without environment configuration.

#### 6a. Directory structure template

```
第X章/                              # chapter directory
├── code/
│   └── chapter_X.py               # all code examples
├── data/
│   ├── dataset.csv                 # labeled data
│   ├── vocab.txt                   # dictionaries, stopwords, etc.
│   └── ...                         # any data the code needs
├── pyproject.toml                  # [MANDATORY] uv-ready dependency config
├── requirements.txt                # [MANDATORY] pip fallback
└── README.md                       # [MANDATORY] run instructions
```

#### 6b. Create dependency config

- **`pyproject.toml`**: Minimal project config with ALL dependencies for THIS chapter. Group deps by chapter with comments (`# 第X章：xxx`).
  ```toml
  [project]
  name = "chapterX-topic"
  version = "1.0.0"
  description = "第X章 主题 - 课程作业"
  requires-python = ">=3.10"
  dependencies = [
      "jieba>=0.42.1",
      "scikit-learn>=1.3.0",
      # ... all deps needed by this chapter
  ]
  ```
- **`requirements.txt`**: Flat list of `package>=version` for `pip install -r requirements.txt`

#### 6c. Create README.md

Include:
- Two installation methods (uv + pip) with exact commands
- File structure listing
- Notes about any special behavior (pop-up charts, slow first-run downloads)

For a reusable README template with `{{PLACEHOLDERS}}`, see `templates/chapter-README.md`.

#### 6d. 7z packaging

```bash
7z a -t7z -mx=5 输出文件名.7z  要打包的目录 \
  -xr!".venv" -xr!"node_modules" -xr!".git" \
  -xr!"__pycache__" -xr!"*.pyc"
```

When the user says "只要X章就好了", only package that specific directory.

**Do NOT include:**
- Other chapters' directories
- The main course project (unless explicitly requested)
- `.venv/`, `node_modules/`, `.git/`, `__pycache__/`, `*.pyc`
- Large model weight files (unless the teacher needs them to run)

## Reading PPTX slide content (without python-pptx)

When you need to read textbook PPT slides to understand chapter requirements but python-pptx is not installed:

```python
import zipfile, re

with zipfile.ZipFile('文件.pptx') as z:
    slides = [f for f in z.namelist() if f.startswith('ppt/slides/slide') and f.endswith('.xml')]
    slides.sort()
    for slide_path in slides[:20]:  # limit to first 20 slides
        content = z.read(slide_path).decode('utf-8')
        texts = re.findall(r'<a:t[^>]*>([^<]+)</a:t>', content)
        text = ' '.join(texts)
        if text.strip():
            print(f'--- Slide N ---')
            print(text)
```

This extracts text from all `<a:t>` (text) elements in each slide's XML without any external dependency.

## Files likely to change

- `第X章/code/chapter_X.py` — the main code file
- `第X章/data/` — data files
- `pyproject.toml` — when adding new dependencies

## Verification

After setup, verify by:
1. (Optional) Run `python chapter_X.py` in the code directory to confirm no ImportError or SyntaxError
2. Confirm directory structure matches existing chapters
3. Confirm all data files referenced in the code exist
4. If packaging for submission, confirm `pyproject.toml`, `requirements.txt`, and `README.md` are present

## References

- `references/pptx-text-extraction.md` — extracting text from PPTX slides using zipfile (no python-pptx)
- `references/archive-inspection-fallback.md` — zero-dependency inspection for DOCX, RAR, ZIP, and PPTX (absorbed from `document-inspection` skill)
- `references/matplotlib-dpi-for-screens.md` — fixing textbook code's print-resolution DPI for screen display
- `references/csv-data-for-submissions.md` — CSV format conventions, encoding, and data distribution best practices for teacher-submitted data
- `templates/chapter-README.md` — reusable README template with `{{PLACEHOLDERS}}`
- `templates/chapter-data.csv` — sample CSV for student data exercises
- `templates/chapter-pyproject.toml` — sample pyproject.toml template
- `templates/chapter-requirements.txt` — sample requirements.txt template
