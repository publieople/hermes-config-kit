---
name: liciyuan-api
description: 栗次元API (t.alcy.cc) — 免费随机图片API，17个分类。支持直接返回图片(302重定向)或JSON格式。适合做壁纸、头像、背景图。
trigger: 栗次元|liciyuan|t.alcy.cc|随机图片|随机壁纸|随机头像|随机背景图
---

# 栗次元API (Liciyuan API)

**Base URL:** `https://t.alcy.cc`

免费随机图片API，由"举个栗子"维护。每个分类有数百张图，持续更新。

## 两种调用方式

### 1️⃣ 直接图片（302重定向到图片）

```
GET https://t.alcy.cc/{category}
```

直接返回 302 重定向到随机图片。浏览器打开直接看到图，curl 加 `-L` 跟随即可。

```bash
curl -sL "https://t.alcy.cc/pc" > image.webp
```

### 2️⃣ JSON 格式

```
GET https://t.alcy.cc/json/?{category}
GET https://t.alcy.cc/json/?{category}={count}
```

> ⚠️ `json` 后面必须有 `/`，否则会 301 跳转。

返回 JSON：

```json
{
  "code": 200,
  "category": "pc",
  "count": 1,
  "data": {
    "id": 826,
    "link": "https://tc.alcy.cc/tc/20260121/xxx.webp"
  }
}
```

多条模式返回的 `data` 是数组，同时额外提供 `links` 字段（纯URL数组）。

## 分类一览

| 参数名 | 名称 | 类型 | 示例 |
|--------|------|------|------|
| `pc` | PC横图 | 横图(桌面壁纸) | `?pc` / `?pc=3` |
| `moe` | 萌版横图 | 横图 | `?moe` |
| `fj` | 风景横图 | 横图 | `?fj` |
| `bd` | 白底横图 | 横图 | `?bd` |
| `ys` | 原神横图 | 横图 | `?ys` |
| `ai` | AI自适应 | 横图 | `?ai` |
| `mp` | 移动竖图 | 竖图(手机壁纸) | `?mp` |
| `moemp` | 萌版竖图 | 竖图 | `?moemp` |
| `ysmp` | 原神竖图 | 竖图 | `?ysmp` |
| `aimp` | AI竖图 | 竖图 | `?aimp` |
| `fjmp` | 风景竖图 | 竖图 | `?fjmp` |
| `tx` | 头像方图 | 正方形(头像) | `?tx` |
| `lai` | 七濑胡桃 | 特定角色 | `?lai` |
| `xhl` | 小狐狸 | 特定角色 | `?xhl` |

### 仅直接图片可用（JSON不支持）

| 路径 | 说明 |
|------|------|
| `/ycy` | YCY |
| `/moez` | 萌版自适应 |
| `/ysz` | 原神自适应 |
| `/acg` | ACG动图 |

### 外部Pixiv

```
https://pivix.mwm.moe/api/v2/img
```

海量随机Pixiv图片，质量无保障，有一定算法优选。参数文档见 pivix.mwm.moe。

## 快速命令

```bash
# 获取一张PC横图 (JSON)
curl -sL "https://t.alcy.cc/json/?pc"

# 获取3张AI竖图 (JSON)
curl -sL "https://t.alcy.cc/json/?aimp=3"

# 直接下载一张风景图
curl -sL "https://t.alcy.cc/fj" -o wallpaper.webp

# 获取Genshin Impact手机壁纸
curl -sL "https://t.alcy.cc/json/?ysmp"
```

## 注意事项

1. 图片存储在 `tc.alcy.cc` CDN 上，由腾讯EdgeOne/雨云提供加速
2. 有免费CDN额度，合理使用即可
3. 图片格式主要为 webp
4. 各分类图库持续更新（详情看改动日志）
