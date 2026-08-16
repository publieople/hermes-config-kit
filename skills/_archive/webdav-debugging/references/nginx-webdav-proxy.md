# OpenList WebDAV Nginx 代理配置模板

## 完整 root.conf（用于 1Panel 站点代理）

```
location ^~ / {
    proxy_pass http://172.17.0.1:5244;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "";
    set_by_lua_block $rewritten_dest {
        local dest = ngx.var.http_destination
        if dest then
            dest = dest:gsub("^https?://[^/]+", "")
        end
        return dest or ""
    }
    proxy_set_header Destination $rewritten_dest;
    client_max_body_size 0;
    proxy_request_buffering off;
    proxy_buffering off;
    proxy_read_timeout 300s;
    proxy_send_timeout 300s;
}
```

## 关键配置说明

| 配置项 | 作用 | 缺失后果 |
|--------|------|----------|
| `proxy_pass http://172.17.0.1:5244` | Docker 网桥网关（不用 host.docker.internal） | 容器重启丢 /etc/hosts |
| `set_by_lua_block $rewritten_dest` | 剥离 Destination 头的 scheme+host | OpenList 拒绝绝对 URL → 502 |
| `proxy_set_header Destination $rewritten_dest` | 转发改写后的 Destination | 同上 |
| `client_max_body_size 0` | 不限制上传大小 | 大文件上传被截断 |
| `proxy_request_buffering off` | 关闭请求缓冲 | WebDAV 大文件卡住 |
| `proxy_buffering off` | 关闭代理缓冲 | 流式传输延迟 |
| `proxy_read_timeout 300s` | 上游响应超时 | 大文件 MOVE 超时 |

## 为什么用 Lua 改写 Destination

OpenList（及 AList）不接受 RFC 4918 标准允许的绝对 URL `Destination: http://sync.ai.for-people.cn:8080/dav/...`。

`set_by_lua_block` 是 OpenResty 内置功能，无需额外模块。它在 access 阶段执行，在 proxy_pass 之前改写 header。

## 部署步骤

```fish
# 从容器拉配置
sudo docker cp (容器名):/www/sites/(域名)/proxy/root.conf /tmp/root.conf

# python3 修改（fish 不支持 bash heredoc）
sudo python3 -c "
c = open('/tmp/root.conf').read()
c = c.replace('proxy_pass http://host.docker.internal', 'proxy_pass http://172.17.0.1')
# 添加 Lua 改写...
open('/tmp/root.conf','w').write(c)
"

# 塞回容器并重载
sudo docker cp /tmp/root.conf (容器名):/www/sites/(域名)/proxy/root.conf
sudo docker exec (容器名) nginx -s reload
```
