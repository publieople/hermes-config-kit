# WebDAV 同步替代方案

调研于 2026-06-07，对比坚果云免费版的替代方案。

## 坚果云限制

- 上传 1GB/月，下载 3GB/月
- 30 分钟 600 次请求限制
- 对剪贴板高频同步场景不够用

## 方案对比

### 1. InfiniCLOUD（原 TeraCLOUD）⭐ 最推荐

日本老牌网盘，国内访问速度不错。

| 项 | 值 |
|----|-----|
| 免费空间 | 20GB（+ 邀请码 5GB = 25GB）|
| 流量限制 | **不限** |
| 请求限制 | **无** |
| WebDAV | ✅ |
| 注册 | https://infini-cloud.net |
| 邀请码 | `RYCH7`（+5GB）|

配置：My Page → Apps Connection → 勾选开启 → 生成 WebDAV 密码。TieZ 填 `https://xxxx.infinicloud.com/dav/`。

### 2. OpenList（自建 WebDAV）

AList 于 2025-04 被出售给贵州"不够科技"，社区 fork 出 OpenList：

- 仓库：https://github.com/OpenListTeam/OpenList
- 许可：AGPL-3.0，社区驱动，无商业化
- 已审计近半年代码，确认无恶意代码
- Docker 部署：`docker run -d --name openlist -p 5244:5244 openlistteam/openlist:latest`

**AList 出售争议**：
- 新东家修改文档加商业链接
- PR #8633 试图收集用户 OS 信息上传私有地址（已撤回）
- 原开发者 Xhofe 退出社群，仅承诺审查开源代码

### 3. MQTT（TieZ 原生支持）

TieZ 支持 MQTT 同步，绕过 WebDAV 流量限制。

免费公共 broker：
- EMQX：`broker-cn.emqx.io:1883`（中国节点）
- ⚠️ 公共 broker 消息所有人可见

自建 Mosquitto（VPS/NAS）轻量无限制。

### 4. Syncthing P2P

设备直连同步 TieZ 数据目录，零成本。

缺点：需两台设备同时在线。

### 5. CloudDrive2

网盘挂载到本地磁盘，支持阿里云盘/115。

非开源但免费。

## 推荐排序

对于 TieZ 剪贴板同步：
1. **InfiniCLOUD** — 最省事，注册即用，跟坚果云体验一样
2. **OpenList 自建** — 有服务器的话，完全自主可控
3. **MQTT** — TieZ 原生支持，自建 broker 最佳
