# 1Panel WAF siteConfig.json 结构

路径：`/usr/local/openresty/1pwaf/data/conf/siteConfig.json`

```json
{
  "methodWhite": {
    "state": "on",
    "methods": ["GET", "POST", "HEAD", "PUT", "DELETE", "OPTIONS", "PATCH"]
  },
  "header": {
    "state": "on",
    "rules": [...]
  },
  "xss": {
    "state": "on",
    "rules": [...]
  },
  "sql": { "state": "on", "rules": [...] },
  "url": { "state": "on", "rules": [...] },
  "cookie": { "state": "on", "rules": [...] },
  "args": { "state": "on", "rules": [...] },
  "userAgent": { "state": "on", "rules": [...] }
}
```

## WebDAV 冲突规则详解

### methodWhite
- MOVE, PROPFIND, MKCOL, LOCK, UNLOCK, COPY 不在白名单 → 拦截
- 关闭：`cfg.methodWhite.state = "off"`

### header
- MOVE 请求携带 `Destination` 头，值为完整 URL（如 `http://sync.ai.for-people.cn:8080/dav/...`）
- WAF 的 header 规则可能将此 URL 视为恶意请求 → 拦截
- 关闭：`cfg.header.state = "off"`

### xss
- PROPFIND 请求 body 是 XML，触发 XSS 检测 → 拦截
- 关闭：`cfg.xss.state = "off"`
