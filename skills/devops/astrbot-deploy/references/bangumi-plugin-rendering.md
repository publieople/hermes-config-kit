# Bangumi 插件 Pillow 渲染故障排查

`astrbot_plugin_bangumi_enhance` (united-pooh) 的图片生成依赖 CJK 字体。渲染链为 RPC → 本地 Playwright → Pillow 兜底。

## 症状

- 返回的图片是**空白/纯白**（2400×1674，75%+ 白色像素，无文字内容）
- `render_mode` 默认 `html`，但在国内环境下 RPC 和 Playwright 都可能失败，最终走 Pillow
- Pillow 的 `get_font()` 找不到 CJK 字体时降级到 `ImageFont.load_default()`，无法渲染中文

## 根因

1. 插件初始化时后台线程从 GitHub 下载 NotoSansCJK 字体 → 国内无代理直连 GitHub 必超时
2. 系统字体候选列表不含 Arch/WSL 常见的 SimHei 路径，只有 macOS 和标准 Linux 路径
3. `fonts/` 目录空 → `_downloaded_font_candidates()` 返回空 → `_REGULAR_FONT_CANDIDATES` 里的路径不存在 → 最终 fallback 到 `load_default()`

## 诊断命令

```bash
# 检查字体目录是否为空
ls -la ~/astrbot/data/plugin_data/astrbot_plugin_bangumi_enhance/fonts/

# 检查系统 CJK 字体
fc-list :lang=zh

# 验证 SimHei 能否被 PIL 加载
python3 -c "from PIL import ImageFont; f=ImageFont.truetype('/home/po/.local/share/fonts/simhei.ttf',42); print('OK:', f)"

# 检查图片是否空白（非白色像素占比）
python3 -c "
from PIL import Image; from collections import Counter
img=Image.open('图片路径'); c=Counter(img.getdata())
white=c.get((255,255,255),0)+c.get((253,253,253),0)
print(f'White: {white/len(list(img.getdata()))*100:.1f}%')
"
```

## 修复方案

### 方案一：复制 Windows 上的 Maple Mono NF CN（用户偏好）

WSL 可直接访问 Windows 字体目录。Maple Mono NF CN 是等宽中文 Nerd Font，CJK 字形覆盖完整：

```bash
FONT_DIR=~/astrbot/data/plugin_data/astrbot_plugin_bangumi_enhance/fonts
WIN_FONTS="/mnt/c/Windows/Fonts"

# Regular: Italic 变体（CJK 字形几乎不受斜体影响）
cp "$WIN_FONTS/MapleMonoNormal-NF-CN-Italic.ttf" "$FONT_DIR/NotoSansCJKsc-Regular.otf"
# Bold: Bold 变体（非斜体）
cp "$WIN_FONTS/MapleMonoNormal-NF-CN-Bold.ttf" "$FONT_DIR/NotoSansCJKsc-Bold.otf"
```

⚠️ Maple NF CN 只有 Italic/Bold/ExtraLight 等变体，无 Regular 非斜体版本。用 Italic 替代 Regular 完全可用。

### 方案二：软链已有 SimHei（最快）

```bash
FONT_DIR=~/astrbot/data/plugin_data/astrbot_plugin_bangumi_enhance/fonts
ln -s /home/po/.local/share/fonts/simhei.ttf "$FONT_DIR/NotoSansCJKsc-Regular.otf"
ln -s /home/po/.local/share/fonts/simhei.ttf "$FONT_DIR/NotoSansCJKsc-Bold.otf"
```

重启 AstrBot 后生效。

### 方案三：切到 pillow 渲染模式 + skip RPC/Playwright

插件默认 `render_mode: html`，渲染链为 RPC(境外) → Playwright(需 Chromium) → Pillow 兜底。在国内/WSL 环境下前两级大概率超时。改为 `pillow` 跳过前两级：

修改 `astrbot_plugin_bangumi_enhance_config.json` 中的 `render_mode` 为 `pillow`，或在 WebUI 插件配置中修改。

同时可 patch `pillow_utils.py` 的 `_REGULAR_FONT_CANDIDATES` 和 `_BOLD_FONT_CANDIDATES`，在列表前面加入系统已有字体路径。

### 方案四：手动下载 NotoSansCJK（有代理时）

```bash
FONT_DIR=~/astrbot/data/plugin_data/astrbot_plugin_bangumi_enhance/fonts
export https_proxy=http://127.0.0.1:7890
curl -L -o "$FONT_DIR/NotoSansCJKsc-Regular.otf" \
  "https://github.com/notofonts/noto-cjk/raw/main/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Regular.otf"
curl -L -o "$FONT_DIR/NotoSansCJKsc-Bold.otf" \
  "https://github.com/notofonts/noto-cjk/raw/main/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Bold.otf"
```

## 插件架构（追番机制）

### 订阅流程

```
用户 /追番 → 搜索 Bangumi API → 校验是否在当季放送表(calendar)中
                                        ↓
                          不在 → ⚠️ 暂不支持自动追踪（已完结/未开播）
                          在   → 写入 SQLite(subscriptions 表): group_id + subject_id + name + current_episode
```

只接受在 Bangumi 每日放送表里的番剧，防止无效订阅。

### 定时检查

插件初始化时注册 APScheduler cron 任务 — `trigger=cron, minute=0`（每小时整点）：

```
check_updates() →
  从 SQLite 读取所有监控中的番剧
  对每个番剧:
    └─ Bangumi API 查最新集数(get_latest_episode)
       └─ 最新集数 > current_episode？
          ├─ 是 → 更新 DB current_episode
          │       → Pillow/HTML 渲染单集更新卡片
          │       → OneBot 推送到订阅群(StarTools.send_message_by_id)
          └─ 否 → 跳过
```

### 渲染失败兜底

卡片渲染失败时降级为纯文字通知：`🔔 《xxx》更新啦！第 N 集: ...`，不会错过更新。

### 数据库

`~/astrbot/data/plugin_data/astrbot_plugin_bangumi_enhance/data.db` — `subscriptions` 表：

| 字段 | 说明 |
|------|------|
| `group_id` | QQ 群号 |
| `subject_id` | Bangumi 条目 ID |
| `name` | 番剧名称 |
| `current_episode` | 已播最新集数 |
| `air_date` | 首播日期 |
| `total_episodes` | 总话数 |

### 性能注意

- 每小时对所有订阅番剧发起 Bangumi API 调用 — N 个订阅 = N 次/小时
- 需配置 `access_token` 避免 API 限流（`_conf_schema.json` → 插件配置）
