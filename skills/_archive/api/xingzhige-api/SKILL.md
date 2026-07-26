---
name: xingzhige-api
description: 星之阁API聚合平台 — 50+免费公开API，涵盖视频解析、音乐搜索、AI绘图、B站工具、娱乐表情生成等。通过 curl 调用。
trigger: 星之阁|xingzhige|星之阁API|xingzhige API|视频解析|短剧搜索|AI绘图|B站解析|抖音解析|网易云音乐|必应壁纸
---

# 星之阁API (Xingzhige API)

**Base URL:** `https://api.xingzhige.com`

所有API返回 JSON 格式：`{"code": 0, "msg": "成功", "data": {...}}`

## 快速查找

当用户说"帮我XXX"时，先根据下表找到对应API ID，然后用 `/API/{slug}/` 端点调用。

---

## 全部 API 一览（48个可用）

### 🎬 视频解析类

| ID | 名称 | 端点 | 参数 | 调用量 |
|----|------|------|------|--------|
| 56 | **短剧搜索** | `/API/playlet/` | `keyword`(必填), `page`, `book_id`, `video_id`, `quality(720p/1080p/original)` | 5271万 |
| 40 | **B站解析** | `/API/b_parse/` | `url`(必填), `access_key`(大会员必填) | 766万 |
| 50 | **看看抖音** | `/API/douyin/` | `url`(必填) — 解析抖音图集/视频 | 633万 |
| 54 | **看看小世界** | `/API/QQxsj/` | `url`(必填) | 6.3万 |
| 53 | **看看西瓜** | `/API/xigua/` | `url`(必填) | 0.2万 |
| 52 | **看看快手** | `/API/kuaishou/` | `url`(必填) — 解析快手图集/视频 | 0.8万 |
| 39 | **B站番剧解析** | `/API/b_bangumi/` | `ss_id`(season_id获取列表), `ep_id`, `access_key`(大会员) | 1.2万 |
| 9 | **B站视频解析** | `/API/b_video/` | `bvid` 或 `aid` — 解析不了番剧 | 2万 |

### 🎵 音乐搜索类

| ID | 名称 | 端点 | 参数 | 调用量 |
|----|------|------|------|--------|
| 46 | **网易音乐搜索** | `/API/NetEase_CloudMusic_new/` | `name`(歌名), `n`(选曲), `page`, `pagesize`, `br`(音质), `songid` | 272万 |
| 48 | **波点音乐搜索** | `/API/Kuwo_BD_new/` | 同上模式 | 54万 |
| 55 | **酷狗/QQ歌词获取** | `/API/(需查doc)` | 获取QRC/KRC/KSC/lyrc歌词 | 29万 |
| 4 | **网易云随机热评** | `/API/NetEase_CloudMusic_hotReview/` | `id`(歌单ID,默认3778678) | 12万 |
| 47 | **酷狗音乐搜索** | 🔧维护中 | — | 60万 |
| 41 | **QQ音乐点歌** | 🔧维护中 | — | 18万 |
| 30 | **网易云音乐搜索(旧)** | 🔧维护中 | — | 70万 |
| 27 | **QQ音乐搜索** | 🔧维护中 | — | 4670万 |

### 🎨 AI/图像类

| ID | 名称 | 端点 | 参数 | 调用量 |
|----|------|------|------|--------|
| 58 | **AI绘图** | `/API/DrawOne/` | `prompt`(必填), `model`(必填), `size`(如2:3), `type=models`获取模型列表 | 6.4万 |
| 59 | **AI风格转变** | `/API/AiStyle/` | `url`(图片直链), `model`(风格: 像素/抽象/韩系淡彩/清新日漫/纯真动漫) | 0.7万 |
| 57 | **AI说话(TTS)** | `/API/AiChat/` | `module`(material_list/task/result), `text`, `voice`, `voice_engine`, `task_id` | 2.8万 |
| 45 | **素描** | `/API/xian/` | `url`(图片链接), `delay`(GIF速度,默认5) | 1.3万 |
| 2 | **Bing每日一图** | `/API/Bing_img/` | 无参数 | 15万 |

### 😂 QQ头像娱乐表情

| ID | 名称 | 端点 | 默认参数 | 调用量 |
|----|------|------|----------|--------|
| 26 | 打年糕 | `/API/pound/` | `qq`(必填) + `type`/`img_url`可选 | 691万 |
| 25 | 舞鸡腿 | `/API/DanceChickenLeg/` | 同上 | 681万 |
| 24 | 招财喵 | `/API/FortuneCat/` | 同上 | 677万 |
| 23 | 一起笑 | `/API/LaughTogether/` | 同上 | 679万 |
| 21 | 抱肉肉 | `/API/baororo/` | 同上 | 96万 |
| 18 | 看这个 | `/API/Lookatthis/` | 同上 | 704万 |
| 17 | 咬 | `/API/bite/` | `qq`(必填) + 同上 | 35万 |
| 16 | 顶球 | `/API/dingqiu/` | 同上 | 699万 |
| 15 | 拍瓜 | `/API/paigua/` | 同上 | 697万 |
| 14 | 抓 | `/API/grab/` | 同上 | 688万 |
| 44 | 可莉吃 | `/API/chi/` | `qq`(必填) | 1.7万 |
| 43 | 爬！ | `/API/pa/` | `qq`(必填) | 179万 |
| 42 | 冰淇淋 | 🔧维护中 | — | 75万 |

**通用参数说明 (表情类):**
- `qq`(必填): 要生成头像的QQ号
- `type=url`: 使用自定义图片
- `img_url`: 自定义图片地址 (当type=url时必填)

### 👤 B站工具

| ID | 名称 | 端点 | 参数 | 调用量 |
|----|------|------|------|--------|
| 37 | **B站用户信息** | `/API/b_personal/` | `mid`(UID,必填) | 166万 |
| 10 | **B站搜索** | `/API/b_search/` | `msg`(搜索内容), `n`(返回数量,默认5) | 165万 |
| 38 | **B站发私信** | `/API/b_msg/` | `mid`, `msg`, `type`(1文字/5撤回), `sessdata`, `csrf` | 0.1万 |
| 20 | **B站扫码登录(tv)** | `/API/b_qrcode/` | `auth_code`(空则获取验证码,非空则验证) | 0.7万 |
| 28 | **B站短链** | 🔧维护中 | — | — |

### 🤖 QQ工具 (需cookie凭证)

| ID | 名称 | 端点 | 说明 | 调用量 |
|----|------|------|------|--------|
| 1 | 群活跃排行 | `/API/group_speak/` | `qq`+`skey`+`pskey`+`group`+`time`+`num` | 1.4万 |
| 5 | 业务查询 | `/API/QQ_Business/` | `qq`+`uin`+`skey`+`pskey` | 0.3万 |
| 6 | 钱包余额 | `/API/QQWallet/` | `uin`+`skey`+`pskey`(tenpay.com域) | 0.3万 |
| 7 | 群成员信息 | 🔧维护中 | — | 350万 |
| 8 | QQ等级查询 | `/API/QQ_level/` | `uin`+`skey`+`pskey`+`qq` | 6.5万 |
| 11 | 修改QQ昵称 | `/API/modify_QQNickname/` | `uin`+`skey`+`pskey`+`name`+`sign` | 0.4万 |
| 12 | 修改群头像 | `/API/group_avatar/` | `uin`+`skey`+`group`+`img_url` | 0.6万 |
| 29 | 获取QQ头像 | `/API/get_QQavatar/` | `qq`, `s`(像素大小:0~5) | 0.8万 |

### 🎲 娱乐/其他

| ID | 名称 | 端点 | 参数 | 调用量 |
|----|------|------|------|--------|
| 34 | 原神黄历 | `/API/yshl/` | 无参数 | 30万 |
| 36 | CP宇宙触发器 | `/API/cp_generate_2/` | `name1`, `name2`, `type`(道具), `data=img`输出图片 | 8.6万 |
| 31 | CP短打生成器 | `/API/cp_generate/` | `g`(攻), `s`(受) | 33万 |
| 32 | 姓名缘分测试 | `/API/yuanfen/` | `name1`, `name2`(不能为英文) | 12万 |
| 49 | 搜索漫画 | `/API/CartoonInn/` | `keyword`, `n`(选书), `nn`(选章) | 0.3万 |
| 51 | 看看动漫 | `/API/anime/` | `msg`(搜索), `n`, `nn`, `type`(线路1/2) | 1.6万 |
| 35 | Minecraft皮肤渲染 | `/API/get_Minecraft_skins/` | `type`(avatar/skin/head3d/body3d/preview/frame), `name`/`uuid`/`skinurl` | 13万 |
| 22 | 签到日历 | `/API/Calendar/` | `Tick`(勾选日期,逗号分隔), `Template`(1~10), `year`, `month` | 14万 |
| 3 | 二维码生成 | `/API/Qrcode/` | `text`(内容) | 167万 |
| 13 | 二维码解析 | 🔧维护中 | — | — |
| 33 | 检讨书生成器 | 🔧维护中 | — | 0.4万 |

---

## 调用方式

### GET 请求（大部分API支持）

```bash
curl -s "https://api.xingzhige.com/API/b_personal/?mid=324858924"
```

### POST 请求（文档数据查询用）

```bash
curl -s -X POST "https://api.xingzhige.com/data/api/index/?type=get_apiData" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "apiId=40"
```

---

## 注意事项

1. **调用频率**：无公开限流说明，但合理使用
2. **维护接口**：`state=0` 的接口(标注🔧)不可用
3. **QQ相关**：需要 `uin`+`skey`+`pskey` 的接口需要用户提供QQ cookie，大多数场景用不到
4. **B站大会员**：解析大会员专属视频需提供 `access_key`
5. **B站私信**：需要 `sessdata`+`csrf`(bili_jct)，一般不推荐使用
6. **表情类API**：返回图片直链，可嵌入 img 标签

## 常用快速命令

```bash
# 1. 获取所有API列表
curl -s "https://api.xingzhige.com/data/api/index/?type=get_apilist"

# 2. 获取某个API的文档（参数信息）
curl -s -X POST "https://api.xingzhige.com/data/api/index/?type=get_apiData" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "apiId=ID"

# 3. Bing每日壁纸
curl -s "https://api.xingzhige.com/API/Bing_img/"

# 4. 网易云音乐搜索
curl -s "https://api.xingzhige.com/API/NetEase_CloudMusic_new/?name=青花瓷"

# 5. B站用户信息 (uid=324858924)
curl -s "https://api.xingzhige.com/API/b_personal/?mid=324858924"

# 6. 抖音视频解析
curl -s "https://api.xingzhige.com/API/douyin/?url=https://v.douyin.com/xxxxx/"
```
