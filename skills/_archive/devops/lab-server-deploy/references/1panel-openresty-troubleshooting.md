---
name: 1panel-openresty-troubleshooting
description: 1Panel OpenResty 反向代理排障 — WAF 规则、容器网络、nginx 配置持久化
---

# 1Panel OpenResty Troubleshooting

排障 1Panel 管理的 OpenResty（Nginx+Lua）反向代理容器，涉及 WAF 拦截、容器网络、配置持久化等问题。

## 触发条件

- 1Panel 反向代理站点返回 502/403
- WebDAV/CALDAV 等非标准 HTTP 方法被拦截
- OpenResty 容器重启后代理失效
- WAF 规则修改后未生效

## 关键路径

| 路径 | 说明 |
|------|------|
| `/www/sites/<domain>/proxy/root.conf` | 站点代理配置（手改持久化处） |
| `/usr/local/openresty/1pwaf/data/conf/siteConfig.json` | WAF 全局配置 |
| `/usr/local/openresty/nginx/conf/conf.d/<domain>.conf` | Nginx 站点配置（1Panel 自动生成，勿手改） |

## WAF 规则排障

### 常见拦截 WebDAV 的规则

1Panel WAF (`siteConfig.json`) 中有三个规则会拦截 WebDAV 的 MOVE/PROPFIND/MKCOL 请求：

| 规则 | 拦截原因 |
|------|---------|
| `methodWhite` | MOVE/PROPFIND/MKCOL 不在 HTTP 方法白名单 |
| `header` | MOVE 的 `Destination` 头含完整 URL，被视为恶意 |
| `xss` | 请求体中的 XML（PROPFIND 的 body）触发 XSS 检测 |

### 关闭方式（推荐 Lua 脚本）

```fish
sudo docker exec <container> resty -e '
local cjson = require "cjson"
local f = io.open("/usr/local/openresty/1pwaf/data/conf/siteConfig.json", "r")
local cfg = cjson.decode(f:read("*a"))
f:close()
cfg.methodWhite.state = "off"
cfg.header.state = "off"
cfg.xss.state = "off"
f = io.open("/usr/local/openresty/1pwaf/data/conf/siteConfig.json", "w")
f:write(cjson.encode(cfg))
f:close()
print("methodWhite=" .. cfg.methodWhite.state .. " header=" .. cfg.header.state .. " xss=" .. cfg.xss.state)
'
```

### ⚠️ 必须 restart，不能 reload

`nginx -s reload` 不清除 Lua 共享内存 (`ngx.shared.DICT`)，WAF 缓存旧配置。修改 `siteConfig.json` 后必须：

```fish
sudo docker restart <container>
```

## 容器网络

### 代理宿主机服务

OpenResty 容器内 `127.0.0.1` 是**容器自身环回**，不是宿主机。

**正确方式**：使用 Docker 网桥网关 IP

```nginx
# /www/sites/<domain>/proxy/root.conf
location / {
    proxy_pass http://172.17.0.1:<port>;  # 宿主机在 docker0 网桥上的地址
    # ... 其他 proxy 配置
}
```

### 不要用 host.docker.internal

`host.docker.internal` 需要 `/etc/hosts` 手动添加条目，容器重启后丢失，导致 nginx 启动失败（`host not found in upstream`）→ crash loop。

`172.17.0.1` 是 Docker 默认网桥网关 IP，跨重启不变。

## WebDAV 代理增强配置

在 `root.conf` 中需要的关键配置：

```nginx
location / {
    proxy_pass http://172.17.0.1:<port>;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header Destination $http_destination;  # WebDAV MOVE 必须
    proxy_http_version 1.1;
    proxy_set_header Connection "";
    proxy_request_buffering off;
    proxy_buffering off;
    proxy_read_timeout 300s;
    proxy_send_timeout 300s;
    client_max_body_size 0;
}
```

## 参考文件

- `references/waf-siteconfig-structure.md` — siteConfig.json 完整结构和 WebDAV 冲突规则详解

## 诊断命令

```fish
# 容器是否在运行
sudo docker ps | grep openresty

# 容器日志（看启动错误）
sudo docker logs --tail 20 <container>

# 容器内 curl 测试（过 nginx，不过 WAF？取决于 WAF 配置的 phase）
sudo docker exec <container> curl -sv -X MOVE \
  -u user:pass \
  -H "Destination: http://domain/dav/path/target" \
  http://localhost:8080/dav/path/source

# 外部测试（过完整链路：nginx + WAF）
curl -sv -X MOVE \
  -u user:pass \
  -H "Destination: http://domain:8080/dav/path/target" \
  http://domain:8080/dav/path/source

# 查看站点 access log
sudo docker exec <container> tail -50 /www/sites/<domain>/log/access.log
```

## 常见故障模式

| 现象 | 根因 | 修复 |
|------|------|------|
| MOVE 返回 502，PUT/PROPFIND 正常 | **先排除 OpenList 兼容性问题**（见下文），再排查 WAF 的 methodWhite/header 规则 | 逐层排查：相对路径 MOVE 测试 → Destination 重写 → WAF 规则 + restart |
| 容器重启后 crash loop，日志 `host not found` | `/etc/hosts` 中的 `host.docker.internal` 丢失 | 换成 `172.17.0.1` |
| WAF 规则已关但仍 502 | 可能是 `nginx -s reload` 不清 Lua 共享内存，也可能是**非 WAF 原因**（见 OpenList 兼容性） | 先测试相对路径 MOVE：curl -X MOVE -H "Destination: /dav/path/target" ... |
| 容器内 curl 正常，外部 curl 502 | WAF 在外部访问路径上生效 | 检查并关闭 WAF 规则 |
| PROPFIND 返回 403/502 | WAF xss 规则拦截 XML body | 关闭 xss 规则 |
| MOVE 502 + error.log 无 WAF 报错 + WAF 或全关仍 502 | **OpenList 不接受 Destination 头里的绝对 URL**（如 `http://domain/dav/...`），只接受相对路径（`/dav/...`） | 在 nginx 中用 `set_by_lua_block` 剥离 scheme+host（见下方 Destination 改写） |

### OpenList WebDAV Destination 兼容性（⚠️ 非 WAF 原因）

OpenList 的 WebDAV 实现对 MOVE 操作的 `Destination` 头要求**相对路径**。TieZ 等客户端发送绝对 URL（`http://domain:8080/dav/path/target`），OpenList 直接返回 502，且不记入 error.log。

**快速测试**（区分 WAF 和 OpenList 兼容性）：
```fish
# 绝对 URL → 可能 502
curl -sv -X MOVE -u user:pass \
  -H "Destination: http://domain:8080/dav/path/target" \
  http://domain:8080/dav/path/source

# 相对路径 → 应 201
curl -sv -X MOVE -u user:pass \
  -H "Destination: /dav/path/target" \
  http://domain:8080/dav/path/source
```

**修复**：在 `root.conf` 中加 Lua 重写，剥离 Destination 头里的 scheme+host：
```nginx
set_by_lua_block $rewritten_dest {
    local dest = ngx.var.http_destination
    if dest then
        dest = dest:gsub("^https?://[^/]+", "")
    end
    return dest or ""
}
proxy_set_header Destination $rewritten_dest;
```

此修改替换原来的 `proxy_set_header Destination $http_destination;`，自动将客户端发的绝对 URL 转换为 OpenList 接受的相对路径。

## 限制

- 此技能不覆盖 1Panel Web UI 操作（因版本不同 UI 布局变化大）
- WAF 日志目录可能不存在（`/usr/local/openresty/1pwaf/data/logs/`），依赖 access.log 排障
