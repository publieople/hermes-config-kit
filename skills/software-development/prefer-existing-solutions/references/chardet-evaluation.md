## 编码检测方案对比 (2026-06-20)

open-any 项目需要自动检测文本文件编码（用户拖入 GB2312 文件时显示乱码）。

### 候选方案

| 候选 | 大小 | 浏览器 | TS | 编码覆盖 | 维护状态 |
|------|------|--------|-----|---------|---------|
| `chardet` | 22 KB | ✅ Uint8Array | ✅ 原生 | 25 种（含 GB18030/Big5/Shift-JIS/EUC-KR） | 活跃 (v2.2.0, 2026) |
| `jschardet` | 更大 | ✅ | 有 .d.ts | ~30 种（Python chardet 端口） | 较慢 (158 commits) |
| 手写 heuristic | 0 | ✅ | ✅ | UTF-8 + GBK（仅 2 种） | 自己维护 |

### 选择

`chardet` — 最小、TypeScript 原生、生态验证充分（1,477 项目依赖）。

### 集成代码

```ts
import chardet from 'chardet';

function bufferToText(buffer: ArrayBuffer): string {
  const uint8 = new Uint8Array(buffer);
  if (uint8.length === 0) return '';

  const results = chardet.analyse(uint8);
  if (results.length > 0 && results[0].confidence >= 50) {
    const encoding = results[0].name.toLowerCase();
    try {
      return new TextDecoder(encoding, { fatal: false }).decode(buffer);
    } catch { /* fall through */ }
  }

  return new TextDecoder('utf-8', { fatal: false }).decode(buffer);
}
```

### 效果

- 手写方案：只覆盖 UTF-8 + GBK（用户报 GB2312 打不开）
- chardet：覆盖 25 种编码，包括中日韩所有常见编码
- 体积增量：gzip 后约 1.3 KB
