# AstrBot 运行时异常诊断

> 启动崩溃 / 配置被破坏类问题见 `references/troubleshooting.md`。本文件只覆盖**已经在运行、但行为异常**的 case: 日志入口选择、LLM 输出泄漏、字段污染。

---

## 1. 日志入口选择 (决策流程图)

诊断第一步永远先确认**进程到底是谁在管**, 再选日志源:

```
问题: "AstrBot 做了 X, 我要看为什么"
        │
        ▼
systemctl --user is-active astrbot
        │
   ┌────┴────┐
   │         │
active    inactive/dead   ← 即使 service 单元存在, 进程可能手动跑
   │         │
   ▼         ▼
journal     ps aux | grep 'astrbot run'
优先        │
   │        ├─ 手动起 → tail -F data/astrbot.log (但先 stat 确认 mtime 新鲜)
   │        └─ nohup/disown 起 → 看 nohup.out / 重定向到的文件
   ▼
journalctl --user -u astrbot.service --since '30 min ago'
   (XDG_RUNTIME_DIR 缺失时: XDG_RUNTIME_DIR=/run/user/$(id -u) journalctl --user -u astrbot ...)
```

### 关键陷阱

- **进程在跑 ≠ service active**。ps 看到 PID 不代表 systemd 接管它。手起的进程不写 journal。
- **`data/astrbot.log` 的 mtime 是真相**。`stat ~/astrbot/data/astrbot.log` → mtime 锁在几天前 → **当前 AstrBot 根本没写这个文件**, 别再 grep 它 (哪怕里面"看起来有内容")。
- **buffer 没 flush**。AstrBot 进程 crash / 被 kill -9 时 buffer 不会刷盘, journalctl 因为实时 pipe 反而能拿到。优先 journal。
- **Hermes 内 sandbox terminal 截断输出**。`terminal(background=true)` / `terminal(command='nohup ... &')` 起 AstrBot, 看不到启动日志也看不到 stderr, 进程可能数秒内静默退出。要长任务用 `execute_code` + `subprocess.Popen(start_new_session=True)` (见 SKILL.md "方法 A")。

### 验证脚本

```bash
# 一条命令确认 AstrBot 进程是否归 systemd 管
PID=$(pgrep -f 'astrbot run' | head -1)
if [ -n "$PID" ]; then
  echo "进程 PID: $PID"
  cat /proc/$PID/status | grep -E '^(Name|Pid|PPid|State)' 
  systemctl --user status astrbot.service --no-pager | head -3
fi
echo "---"
echo "data/astrbot.log mtime:"
stat -c '%y %s' ~/astrbot/data/astrbot.log
```

---

## 2. LLM 输出泄漏到 QQ 消息 (reasoning field 污染)

### 症状

群里看到机器人发出 `<system_decision>...</system_decision>`、`<core_topic>...</core_topic>`、`<reasoning>...</reasoning>`、`<think>...</think>`、`<scratchpad>...</scratchpad>` 这种 XML 标签块, **原文发到群, 没被剥离**。

### 快速鉴别: prompt 字面量排查

```bash
# 1. 全仓 grep 是否真的有