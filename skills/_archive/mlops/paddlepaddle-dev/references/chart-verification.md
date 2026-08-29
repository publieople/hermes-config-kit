# 图表验证：用 MiniMax Vision 检查训练输出

训练脚本生成的图表（训练曲线、预测示例、检测结果、预热/吞吐量图）应该在提交前做视觉验证，尤其关注：

1. **数据正确性** — Loss 下降/Acc 上升趋势、冷启动效应、吞吐量单调性
2. **中文渲染** — 标题、坐标轴标签、图例不出现方块（豆腐块）
3. **布局完整性** — 子图齐全、标签不溢出、颜色对应正确

## 工具

### mmx vision describe

```bash
mmx vision describe --image <path-to-png> --prompt "检查问题描述" --output json --quiet
```

**注意**：Hermes 自带的 `vision_analyze` 工具对本地 PNG 文件有时无法读取。`mmx vision describe` 更可靠。

### 检查清单（按图表类型）

| 图表 | 检查重点 |
|------|----------|
| `training_curves.png` | Loss↓ / Acc↑ 趋势、坐标轴（1-10 epoch）、图例清晰、中文无方块 |
| `sample_predictions.png` | 8 子图齐全、绿色=正确/红色=错误、True/Pred 标签完整 |
| `detection_result_scene*.png` | 检测框绘制、标签文字清晰、图面完整 |
| `warmup_*.png` | 冷启动区 + 标注文本、前3/后3均值对比、中文无方块 |
| `throughput_*.png` | 柱状图数据 vs 标签一致、折线趋势正确、中文无方块 |

### 如果中文显示为方块

确保脚本开头有中文字体配置（参照 step06_classifier.py 的 font_manager 配置块）。不能只靠 `plt.rcParams['font.sans-serif']` 设字体名，需要先用 `font_manager` 检测系统可用字体再 fallback。

## 常见问题

- **step08 生成图表中文全方块** — step08 缺少 step06 里的 `font_manager` 字体检测块，需补上
- **warmup 图标注文字被截断** — 冷启动注释的 `xytext` 偏移量可能不足，调整坐标
