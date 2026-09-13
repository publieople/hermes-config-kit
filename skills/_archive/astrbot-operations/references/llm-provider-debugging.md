# LLM Provider 故障排查

AstrBot 调 LLM 出问题时（"bot 不回我"、"bot 回复错乱"、"bot 调了 tool 但没真执行"、"bot 报"完成"但 ComfyUI 没收到"）几乎都落在这几个根因。本节按出现频率从高到低排。

## 1. `/provider <idx>` 是 session 级，不是全局

**症状**：在群 A 切到 M3 调 LLM 成功；在群 B 同样调 LLM，5 次 429 后失败。

**根因**：`/provider` 命令只更新 AstrBot 进程内**当前会话的 LLM context**。`cmd_config.json:233 default_provider_id` 才是全局默认。新群/新会话默认仍走全局默认。

**诊断**：
```bash
journalctl -u astrbot --since "5 min ago" --no-pager | grep -E "429|FreeUsageLimit|retrying"
```

看到 5 次 `retrying (N/5): Error code: 429 - FreeUsageLimitError` 串起来就确诊。

**修复**（持久）：
```bash
sed -i 's|"default_provider_id": "opencode/deepseek-v4-flash-free"|"default_provider_id": "minimax-token-plan/MiniMax-M3"|' /home/po/astrbot/data/cmd_config.json
sudo systemctl restart astrbot
```

**临时**：`/provider 2`（每个群都要切一次，新会话也得切）。`/new` 切新会话**不继承**上次的 provider（实测有时需重切）。

## 2. antipromptinjector 静默封禁 admin

**症状**：bot 完全不回你消息，包括 `aimg`、`/provider`、`/new` 都没响应。其它人发的消息 bot 正常回复。

**根因**：`astrbot_plugin_antipromptinjector` v3.5.x 有 prompt injection 检测，命中后自动加黑名单。**admin 也会被封**（虽然 `cmd_config.json:371 admins_id` 应该豁免，但实测没有）。封禁时长默认 ~1 小时。

**诊断**：
```bash
journalctl -u astrbot --since "1 hour ago" --no-pager | grep -E "antipromptinjector|封禁|黑名单"
```

看到类似 `[antipromptinjector.main:1673]: 黑名单用户 <qq> 封禁已到期，已自动解封` 即可确诊。

**修复**：
- **等**：到时间自动解封（默认 1 小时）
- **手动解封**（插件命令，具体看 schema）：`/unban <qq>` 或 `/remove_bl <qq>`
- **加白名单**（永久）：`/add_wl <qq>` 然后重启插件
- **彻底关掉**（不推荐）：WebUI → antipromptinjector 设置 → 关闭 LLM 审计 / 关闭自动封禁

**易踩坑**：admin 也会被封，admin 豁免**实测不生效**。发图（特别是带 `<img src="file://...">` 的纯文本图）容易触发 detection。

## 3. LLM 假回执（hallucinated success）

**症状**：bot 在群里说"Workflow「Anima文生图」已加入队列 + 执行完成 + 共1张图片: 第1/1张: <空>"。但 ComfyUI journal 0 个 `got prompt`，output 目录无新图。

**根因**：LLM（特别是 M3 这种 100B+ 模型）有时会**自编** tool call 的结果，或者 promax 内部 callback 提前 fire（worker 还没拿到 image）。**LLM 报告的"成功"是幻觉**。

**诊断**：
```bash
# bot 端
journalctl -u astrbot --since "2 min ago" --no-pager | grep -E "Workflow|执行完成|图片"

# ComfyUI 端（必须对比！）
ssh -i ~/.ssh/id_ed25519 -p 35043 po@3722d01e5a6f.ofalias.com "sudo -n journalctl -u comfyui --since '2 min ago' --no-pager -q" | grep "got prompt"
```

bot 端说"完成" + ComfyUI 端 0 got prompt → 假回执。

**修复**：
- **重新发一次**：临时情况，重试通常正常
- **重启 promax 路径**：`sudo systemctl restart astrbot` 让 promax worker 状态清空
- **如果持续**：`/provider 2` 切到更稳的 LLM（M3 比 deepseek-v4-flash-free 幻觉少），或者换 LLM 看是不是模型问题

## 4. LLM tool docstring = 行为指令

**坑**：写 `@llm_tool(name="x")` 时如果 docstring 写"if user inputs Chinese, translate to English"，LLM **不会**自己翻译——它把这句话当描述，直接把中文当 tool 参数传过去。LLM 看到 docstring 写"Do this"才会照做。

**对比**：
| Docstring 写法 | LLM 行为 |
|----------------|---------|
| "Generate image from prompt. If Chinese, translate." | 直接传中文 prompt（不翻译） |
| "Generate image. **You MUST** translate Chinese → English Danbooru tags before calling. Example: 白毛猫娘 → 1girl, white_hair, cat_ears." | LLM 翻译后传英文 |

**模板**（针对 comfyui_txt2img 等绘图 tool）：
```python
"""<一句话功能>.

<模型> trained on <什么数据>. The user usually speaks Chinese but
this tool requires <什么格式> — translate before calling.

<具体格式规则>:
    "<quality prefix tokens>"

Examples — translate the user's request, do not copy these verbatim:
    user "中文"
    → prompt="english tags, comma, separated"

<可用 tag 列表>

Args:
    <param>(type): <说明>. Required/Optional.
"""
```

**关键点**：
- `<一句话功能>` 之后立即说 "**MUST translate**" 之类的强动词
- 给 `user "中文" → prompt="英文"` 对照例子（**不要写 1-2 个就完事，给 2-3 个覆盖常见 case**）
- 列出 `Useful tags: ...`（避免 LLM 瞎编）
- `Required`/`Optional` 明确标注

**验证**：
- 在群里发图 + "@bot 复刻这张" → bot 调 tool → ComfyUI history node 11 text 字段
- 含英文 Danbooru 标签 + 无 `[MSG_ID:xxx]` 后缀 → 成功
- 含中文原文 → 失败，LLM 没按 docstring 翻译

## 5. /provider 列表里的 👈 标记

`/provider` 列出的列表中，👈 标在**当前正在用的 provider**。这只是当前 session 的当前选择，**不代表全局默认**。看完后若想持久化，按 §1 的 sed 改 `default_provider_id`。

## 6. LLM 端 vs 端侧诊断 checklist

排查 "bot 不画图" 时按这个顺序查：

```bash
# 1. bot 端有收到消息吗？
journalctl -u astrbot --since "1 min ago" --no-pager | grep -E "<group_id>|<user_id>"

# 2. LLM 调了 tool 吗？
journalctl -u astrbot --since "1 min ago" --no-pager | grep -E "comfyui_txt2img|tool|llm_tool|tool_calls|tool result"

# 3. LLM 端 429 没？
journalctl -u astrbot --since "1 min ago" --no-pager | grep -E "429|FreeUsageLimit|retrying"

# 4. bot 被封没？
journalctl -u astrbot --since "1 min ago" --no-pager | grep -E "封禁|黑名单|antiprompt"

# 5. AngelHeart 决策是 "参与" 还是 "不参与"？
journalctl -u astrbot --since "1 min ago" --no-pager | grep -E "决策为|策略:"

# 6. ComfyUI 端有 got prompt 吗？
ssh -i ~/.ssh/id_ed25519 -p 35043 po@3722d01e5a6f.ofalias.com "sudo -n journalctl -u comfyui --since '1 min ago' --no-pager -q" | grep "got prompt"

# 7. ComfyUI 跑成功了吗？
ssh -i ~/.ssh/id_ed25519 -p 35043 po@3722d01e5a6f.ofalias.com "sudo -n journalctl -u comfyui --since '1 min ago' --no-pager -q" | grep -E "Prompt executed|Exception"
```

每步对/错都能立即定位故障层（QQ 网关 / AngelHeart / LLM / promax / ComfyUI / 输出环节），不需要靠猜。

## 7. AstrBot journal 路径（避免再走错）

`/etc/systemd/system/astrbot.service` 是 **system scope**，日志在 system journal：

```bash
sudo journalctl -u astrbot --since "5 min ago" --no-pager
```

`~/.config/systemd/user/astrbot.service`（user scope）的 `journalctl --user -u astrbot` 在当前部署**无 entries**（`-- No entries --`），不要走这条路径。详细原因见 SKILL.md 顶部"用户说'查日志'时,先验证日志在不在写"章节。
