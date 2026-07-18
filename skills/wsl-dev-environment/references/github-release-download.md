# GitHub Release 资产下载的 JWT 签名陷阱

## 症状

从 `https://github.com/<owner>/<repo>/releases/download/<tag>/<asset>` 下载大文件（> 50MB）时：

- 速度极慢（177 KB/s 测速）
- 下到 30-50% 就被掐（一次实测下到 33M / 78M、57M / 78M 卡死）
- **续传完全没用** — `curl -C -` 重试后还是从 0 开始，永远到不了
- `unzip -t` 报 "cannot find zipfile directory"（ZIP 中央目录在末尾，没下到）
- 文件头完整（`file` 识别为 `Java archive data`）但实际不可用

## 根因

GitHub release 资产 URL 走 `release-assets.githubusercontent.com` 这个**带 JWT 签名**的临时链接：

```
location: https://release-assets.githubusercontent.com/...?sp=r&sv=2018-11-09&...&sig=...%3D&jwt=eyJ0eX...&...
```

JWT 有效期约 **5-7 分钟**。每次断点续传，curl 重新发请求，server 看到签名过期就重发整段，于是下载永远停在固定百分比循环。`Content-Length: 0` 的预检响应也带同样签名。

## 解决方案（按推荐度）

### 1. 用 `gh` CLI（最稳，已登录的 WSL 必走）

```bash
gh release download <TAG> --repo <OWNER>/<REPO> --pattern "*.jar" --dir ~/dl/
```

- gh 走 `api.github.com`（无 JWT 限制），会从源 repos 下载
- 但实测 gh 也会卡（5 分钟下到 33M / 78M）—— **WSL + clash 代理**对 GitHub 长连接有速率限制
- 适合 ≤ 50MB 的 release

### 2. Windows 浏览器直接下（WSL 用户首选）

打开 GitHub release 页面 → 点资产链接下载到 `C:\Users\<user>\Downloads\`。Windows 浏览器走系统代理，稳定；WSL 共享 NTFS 挂载盘，下完直接 `cp` 过来：

```bash
# 1. 在 Windows 浏览器下完
# 2. WSL 里拷
cp /mnt/c/Users/po/Downloads/ServerPackCreator-8.1.2.jar ~/spc/spc.jar
```

这是 WSL + 国内网络环境下**最稳的方案**，牺牲 1 次手动点击换 100% 完成率。

### 3. 镜像站（不推荐，仅在选项 1/2 不可用时）

```bash
# gh-proxy 走 Cloudflare CDN，相对稳
curl -L -o spc.jar https://gh-proxy.com/https://github.com/Griefed/ServerPackCreator/releases/download/8.1.2/ServerPackCreator-8.1.2.jar
```

但 gh-proxy 本身也可能限速 / 失效，且对大文件不友好。

### 4. 测速再决定

```bash
curl -sL --connect-timeout 5 -o /dev/null -w "size=%{size_download} time=%{time_total} speed=%{speed_download}\n" \
  https://github.com/<owner>/<repo>/releases/download/<TAG>/<file> --max-time 30
```

- speed > 500KB/s → 选项 1（gh）可走
- speed < 200KB/s → 跳过 curl/gh，直接选项 2（浏览器下）

## 验证下载完整性

JAR / ZIP 容器依赖**末尾的中央目录**。文件头完整不代表可用：

```bash
unzip -t foo.jar 2>&1 | tail -3
# "No errors detected" = OK
# "cannot find zipfile directory" = 末尾缺失，重下
```

size 比 `Content-Length` 小 → 肯定坏。

## 跨平台注意

- 别把大文件直接放在 `/mnt/c/` `/mnt/e/` 等 NTFS 挂载盘上让 JVM 跑，**拷贝到 Linux ext4 文件系统**再操作（`~/work/`），性能差几倍
- 写 `cp` 之前先 `file` 验一下，避免重复拷贝坏文件
