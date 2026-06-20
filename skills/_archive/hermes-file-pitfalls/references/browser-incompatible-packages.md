## 浏览器不兼容 Node 包的识别与替换

### 症状

在浏览器 Console 看到类似报错：

```
Uncaught ReferenceError: global is not defined
Uncaught ReferenceError: process is not defined
Uncaught ReferenceError: Buffer is not defined
```

报错堆栈指向 `node_modules/` 下的某个包 → 该包引用了 Node.js 专属 API。

### 根因

Vite/Rolldown 的 CJS→ESM 预打包只能处理模块格式转换，无法替换运行时的 Node API 引用。Node 包的源码里如果有：

```js
// 这些在浏览器里都炸
if (typeof global !== 'undefined') { ... }
const b = Buffer.from(data)
process.env.NODE_ENV
```

Vite 会警告 `Module "stream" has been externalized` 但不一定报错，运行时才会炸。

### 已验证的替换

| 旧包 | 新包 | 体积 | API 差异 |
|------|------|------|---------|
| `@iarna/toml` | `smol-toml` | ~3KB | 极小：`.parse()` / `.stringify()` 签名相同 |

### 为什么没在 build 时发现

1. TypeScript 类型检查不执行运行时代码
2. Vite dev server 的依赖预打包只做静态分析
3. build 通过（Rolldown 不影响打包），但浏览器运行时 `global` 引用直接抛异常，React 树无法挂载 → 页面白屏
4. 唯一可靠检测：**dev server 启动后在浏览器 F12 Console 查看红色报错**

### 排查流程

```bash
# 1. 启动 dev server
npx vite --host 0.0.0.0

# 2. 浏览器打开 F12 → Console
# 3. 看红色报错 → 定位具体包名 → 该包不兼容浏览器

# 4. 搜索浏览器替代品
# 5. npm install <alternative> && npm uninstall <broken>
```

### 本次会话见证（2026-06-20）

open-any 项目 `src/handlers/yaml.tsx` 使用了 `@iarna/toml`。全部检查通过（`tsc -b` 零错误、`vitest run` 182/182 全绿、`npm run build` 成功），但浏览器打开白屏。F12 Console: `@iarna_toml.js:168 Uncaught ReferenceError: global is not defined`。替换为 `smol-toml` 后立即正常。

核心教训：**build 和 test 都通过≠浏览器能跑。必须实际打开页面检查。**
