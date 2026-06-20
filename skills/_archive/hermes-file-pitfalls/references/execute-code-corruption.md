## 变体：execute_code 内 read_file + write_file 的隐形污染

`execute_code` 内部导入的 `read_file` 返回格式与直接工具调用相同——带行号前缀（`1|content\n2|content`）。如果在 execute_code 里用 `write_file` 写回，**行号前缀被原样写入真实文件**，导致文件损坏：

```python
from hermes_tools import read_file, write_file
content = read_file("/home/po/projects/open-any/src/config.ts")
# content["content"] 是 "1|import ...\n2|const ..." 格式
write_file("/home/po/projects/open-any/src/config.ts", content["content"])
# 行号 + 竖线被写进真实文件 → 每行开头变成 "123|actual code"
```

**症状：** 被 `execute_code` 重写的 `.tsx/.ts` 文件出现大面积 `Expression expected`、`Declaration or statement expected` 等 TS 解析错误。

**恢复：** `git checkout -- <file>` 立即回滚。本会话中 csv.tsx/json.tsx/text.tsx/svg.tsx 四文件因此损坏，靠 git checkout 恢复。

**正确做法：** 不要在 `execute_code` 里走 read_file → write_file 流程。替代方案：
1. `terminal` + `sed` 做小改动
2. 回到宿主工具链用 `patch` / `write_file`（注意核心坑 2 的转义问题）
