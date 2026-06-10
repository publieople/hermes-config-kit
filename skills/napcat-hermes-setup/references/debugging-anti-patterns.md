# 调试反模式

## 截断陷阱

**用 `list(d.keys())[:10]` 截断排查 payload 字段 → 隐藏了关键字段。**

典型案例：NapCat 消息有 16 个 key，`[:10]` 截断把 `message` 和 `group_id` 都藏掉了，导致错误推断"消息缺少 message 字段"。实际上数据完整，调试代码有 bug。

正确做法：`sorted(d.keys())` 看全部 key，不要截断。

## 重启陷阱

**`hermes gateway restart` 可能因为 Telegram 连接超时卡死（30s 超时）。**

解决：`kill -9 $(pgrep -f 'hermes_cli.main gateway run')`，等 systemd auto-restart。

## 终端截断

**Heredoc、echo、grep 可能截断长字符串。**

确认 .env 关键变量完整性时用 Python：
```python
python3 -c "
with open('/home/po/.hermes/.env') as f:
    for line in f:
        if 'NAPCAT_TOKEN' in line:
            print(f'len={len(line.strip().split(\"=\",1)[1])}')
"
```

## 双份 Skill 文件冲突

`skill_manage(action='edit')` 写入 `~/.hermes/skills/`，但 repo 源文件在 `~/.hermes/hermes-agent/skills/`。两个路径可能加载不同版本。

解决：修改后确认线数一致：
```bash
wc -l ~/.hermes/skills/<name>/SKILL.md ~/.hermes/hermes-agent/skills/<name>/SKILL.md
```
如有差异，`cp` 同步或删除 skills 目录副本。
