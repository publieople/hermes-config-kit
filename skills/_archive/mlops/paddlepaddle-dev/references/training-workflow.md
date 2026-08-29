# 实训作业处理流程

教师材料的典型结构：
```
老师发的/dayN/
├── 学生任务书_UnitN.docx     ← 任务书（填空形式）
├── HelloPaddleN.py           ← 教师参考代码
├── step0N_xxx.py             ← 学生待运行的步骤脚本
├── step0N_yyy.py
└── 课件.pptx / python-xxx.exe ← 课件和安装包（作业包中排除）
```

## 处理流程

1. **阅读任务书** — 提取 .docx 文本，确认几个任务、填空位置
2. **运行步骤脚本** — 按顺序执行，记录关键输出（shape、值、accuracy）
3. **检查结果合理性** — 如准确率超过 100%，说明数据格式有问题（参看 skill 踩坑部分）
4. **填写答案** — 生成 `答案_UnitN.md`，如实记录运行输出
5. **打包提交** — 排除 `.venv/`、`.git/`、`.exe`、`.pptx`，zip 到 `submission/`

## 常见问题

- **Python 版本不匹配**：教师提供的 `.exe` 安装包是 Windows 版，WSL 用 `uv venv` 创建对应版本即可
- **ppsx 文件和 exe 文件**：不提交，zip 时排除
- **线性回归不收敛**：Paddle 3.3 的 SGD 默认参数可能与教师版本(3.0)不同，如实记录并附说明
- **matplotlib 中文方块**：`fc-list :lang=zh` 确认有 SimHei/NotoSansCJK 字体，在 `import matplotlib.pyplot` 前配置 `font.sans-serif`。详见 skill 主体「matplotlib 中文字体」节。
- **Python 3.11+ 裸泛型类型注解报错**：教师代码中 `Tuple[Dict, List, Optional]` 的 `List` 和 `Optional` 不带类型参数在 Python 3.11+ 触发 `TypeError: Plain typing.Optional is not valid as type argument`。修复：补全类型参数，如 `Tuple[Dict, List[Dict], Optional[Any]]`。搜索修复命令：`search_files` 匹配 `List,\s*Optional\]` 或裸 `Tuple\[.*,\s*List\s*\]` 模式。
- **Unit5 (具身智能) 的特殊性**：4 个 Python 文件都是自包含的，内置 MockRobot/MockVision 模拟组件，`demo_mode=True` 默认开启。无需 PaddlePaddle 环境，`python3 file.py` 即可运行。只需 numpy，cv2 可选（有 fallback）。

## python-docx 填空替换的坑

用 `python-docx` 给任务书填空时，**不要用"搜索下划线长度"策略来定位填空位置**。

❌ 错误做法（v1 — 模糊匹配）：按 `______` → `____` → `___` 降序搜索 paragraph.text，匹配后找 run 替换。这会导致：
- `self.______(img)` 中的 6 下划线先于 `samples[____]` 中的 4 下划线被匹配
- 填入错位（本该填 `'idx'` 的填到了 `self.idx(img)`，本该填 `'transform'` 的没填上）

❌ 错误做法（v1.5 — 顺序替换）：从左到右替换 paragraph.text 中的下划线，然后映射回 run。问题在于 paragraph.text 是 runs 拼接的，下划线可能跨 run 边界，映射关系不可靠。

✅ 正确做法（v2 — Run 级精确定位）：
1. **先打印每个 paragraph 的 run 结构**，精确到 run 索引和内容：
   ```python
   for i, run in enumerate(para.runs):
       if run.text.strip():
           print(f"Run[{i}]: '{run.text[:80]}'")
   ```
2. **按 paragraph_index + run_index 直接定位**，用 `re.sub(r'_{3,}', answer, run.text, count=1)` 替换
3. 单 run 多空时用辅助函数按顺序填入：
   ```python
   def replace_underscores(text, *answers):
       for ans in answers:
           text = re.sub(r'_{3,}', str(ans), text, count=1)
       return text
   ```
4. 替换后**逐段全量验证**：重新加载文件，检查每个预期值是否出现在对应段落中
5. 扫描全文确保无残留 `_{3,}` 下划线
6. 错位时直接**重建段落内容**（清空 runs，写回正确文本）比修补更快

详见 docx skill: `references/template-filling-pitfalls.md`

## Unit 2 特殊模式

教师 Unit 2 材料通常包含两个演示脚本：
- `step04_transforms.py` — 生成变换对比图，保存到 `docs/` 目录。脚本内部路径用 `os.path.dirname(__file__)` 相对定位
- `step05_dataset.py` — 在脚本同级目录下生成 `synthetic_terrain_data/` 合成数据集，同样输出图到 `docs/`

处理时注意事项：
- 两个脚本需要在 unit02_workspace 目录下运行（它们的相对路径依赖）
- 合成数据集每类 10 张，4 类共 40 张，文件小（1-114KB）
- 生成的图表约 7MB（4 张 PNG），打包 zip 时酌情保留
