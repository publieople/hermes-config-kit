# rmcp 3.1 完整坑位（BootKeeper M4 实战实录）

写于 2026-08-03，rmcp 3.1.0 + schemars 1.0 + tokio 实测。全部是编译错误或进程行为换来的。

## 1. Cargo features：没有 server-stdio

```toml
rmcp = { version = "3.1", features = ["server", "transport-io", "macros"] }
```

- `server-stdio` **不存在** → `failed to select a version for rmcp which could resolve this conflict`
- 真实 features 列表（查法，避免猜）：
  ```bash
  curl -sL "https://crates.io/api/v1/crates/rmcp/3.1.0" | jq '.version.features | keys'
  ```
  server 相关：`server`、`transport-io`（stdio）、`transport-async-rw`、`transport-streamable-http-server`、`macros`

## 2. schemars 版本不匹配（trait bound unsatisfied）

rmcp 3.1 依赖 schemars **1.0**（Cargo.toml 里 `[dependencies.schemars] version = "1.0"`）。

- 用 `schemars = "0.8"` derive 的 `JsonSchema` → `Parameters<CategoryFilter>: rmcp::schemars::JsonSchema not satisfied`
- 两个方案都行：
  - 独立 `schemars = { version = "1.0", features = ["derive"] }`，`use schemars::JsonSchema;`
  - 或 `use rmcp::schemars::JsonSchema;`（但 derive 宏仍需独立 schemars 开 derive feature）

## 3. RunningService::waiting() —— 进程 init 后立即退出

最隐蔽的坑。症状：

- init 握手响应**正常**（说明 server 活着）
- 但 tools/list 请求时 **BrokenPipe**（进程已退出）
- 原因：`serve(stdio()).await?` 返回 `RunningService`，main 函数结束 → `RunningService` drop → 连接关闭 → 进程退出

```rust
// ❌ 错误：init 能响应，但后续请求全 BrokenPipe
let server = MyServer::new();
server.serve(rmcp::transport::io::stdio()).await?;
Ok(())

// ✅ 正确：waiting() 阻塞直到连接关闭
let running = MyServer::new().serve(rmcp::transport::io::stdio()).await?;
running.waiting().await?;
```

`waiting(mut self)` 消费 self，阻塞到 service loop 终止（EOF/cancel/error）。

## 4. 宏模式：无 #[tool(aggr)] 属性

- 参数直接用 `Parameters<T>` 类型，**不加** `#[tool(aggr)]`（这个 attribute 不存在，编译报 `expected non-macro attribute`）
- 工具方法返回 `String`（JSON 文本）→ MCP 自动包成 text content
- `#[tool(name = "...", description = "...")]` 里的 description 就是 agent 看到的工具说明，写清楚参数来源（"id from list_items output"）
- `#[tool_handler(router = self.tool_router)]` 挂在 ServerHandler impl 上；`#[tool_router(router = tool_router)]` 挂在工具 impl 上；结构体字段 `tool_router: ToolRouter<Self>` + `new()` 里 `Self::tool_router()`

## 5. stdio 传输是 JSON-Lines

- 每行一个 JSON-RPC 消息 + `\n`（**不是** Content-Length 帧，虽然 MCP 规范写过 LSP 风格帧）
- 客户端测试：python select + readline 最稳
- 测试顺序：initialize → notifications/initialized → tools/list → tools/call
- protocolVersion 用 `2024-11-05`（rmcp 测试里用的就是这个；`2025-06-18` 也能握手但 2024-11-05 更保险）

## 6. 工具返回 JSON 文本的约定

每个 tool 返回 `String`，内部用 `serde_json::to_string(&value).unwrap_or_else(|e| format!("{{\"error\":\"{e}\"}}"))`——错误也返回 JSON 而非 panic，agent 能解析。

## 7. 硬确认写工具

写工具（disable/enable/remove/restore）内部委托共享 launcher（ShellExecuteW runas → helper 弹窗 → 用户确认 → 执行），tool 描述里明确写"user MUST approve, otherwise nothing happens"。MCP 层不 bypass 确认——AI 只能发起，不能绕过。

## 8. 平台隔离

```rust
#[cfg(windows)] { /* 真实枚举/写操作 */ }
#[cfg(not(windows))] { "[]".to_string() }   // 或 error JSON
```

Linux 上编译通过、返回空数组，Windows runner 真跑。
