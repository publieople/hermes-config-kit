# 第X章 主题 — 运行说明

## 方式一：使用 uv（推荐，速度快）

1. 安装 uv：https://docs.astral.sh/uv/
2. 在此目录下执行：

```bash
uv sync
uv run code/chapter_X.py
```

## 方式二：使用 pip

```bash
pip install -r requirements.txt
python code/chapter_X.py
```

## 文件结构

```
第X章/
├── code/
│   └── chapter_X.py        # 主程序
├── data/                    # 所需数据文件
│   └── ...
├── pyproject.toml           # 依赖配置（uv 用）
├── requirements.txt         # 依赖清单（pip 用）
└── README.md                # 本文件
```

## 说明

- 所有代码按顺序执行，结果打印在终端
- 如有图表窗口会弹出，关闭后继续运行
