# manual_lock 列：保护用户手填值不被自动刷新覆盖

## Scenario

字段同时被「系统自动同步」和「用户手动设置」两条路径写入。
`/刷新放送` 类命令走自动同步路径，`overwrite=True` 会无差别 batch_update
覆盖 DB——吞掉用户手填的值。

适用场景：
- 番剧放送时间（bgmlist 误 → 用户手填正确值 → `/刷新放送` 被覆盖）
- 用户自定义模板（系统推荐 + 用户覆写）
- 用户偏好的通知服务器（系统轮询 + 用户钉死某个）
- 用户配置的限速阈值（系统动态调整 + 用户硬设）

## 反模式：靠"非空跳过"区分自动 vs 手动

```python
# 在 _auto_fill_broadcast_times 里:
if not overwrite and subject.broadcast_time and subject.broadcast_weekday:
    continue  # 已有值就跳过
```

这只能避免**自动刷覆盖自动**。`/刷新放送` 走 `overwrite=True`
(`_auto_fill_broadcast_times(overwrite=True)`)，或者任何显式
`batch_update_broadcast_times` 调用，都会绕过这个 skip 把用户手填值
吞掉。错的根本原因：skip 逻辑在**调用方**而非**写入器**，每个调用方都得
自己记得加检查。

**真实事故**（astrbot-plugin-bangumi PR #18 之后）：用户手动设了某部番的
精确放送时间（bgmlist 给错），重启 AstrBot 时填充跳过的（好）；订阅成功后
填充也跳过的（好）；但 `/刷新放送` 把所有已订阅番剧无差别刷成 bgmlist
值（坏，手填被吞）。**信号**：发现 `overwrite=True` / `refresh_all` /
`force_update` 类入口存在 → 这条命令就是吞手填值的入口。

## 正解：manual_lock BOOL 列 + 写入器底层守一道

### 1. Schema 加列

```python
# src/db/models.py
broadcast_manual: Mapped[bool] = mapped_column(
    Boolean, default=False, server_default="0", nullable=False
)  # 手动锁定: True 时自动刷新跳过。手动设值自动 True; 清空自动 False
```

`default=False` + `server_default="0"` 双写——SQLAlchemy 新 insert 不传字段
走 Python default；老 DB 行迁移后 server_default 兜底。**不要用 nullable
int**——bool 两态（True=锁定/False=未锁）比 int 三态（0/1/None）少一类边界。

### 2. 迁移

```bash
sqlite3 data/plugin_data/<plugin>/data.db \
  "ALTER TABLE bangumi_subjects ADD COLUMN broadcast_manual BOOLEAN NOT NULL DEFAULT 0;"
```

或代码内迁移（参考 `astrbot-plugin-bangumi` 的 `_run_migrations` 模式）：

```python
if not _has_column(engine, "bangumi_subjects", "broadcast_manual"):
    from sqlalchemy import text
    with engine.begin() as conn:
        conn.execute(text(
            "ALTER TABLE bangumi_subjects "
            "ADD COLUMN broadcast_manual BOOLEAN NOT NULL DEFAULT 0"
        ))
```

老行 `broadcast_manual = False`（未锁定）——向后兼容默认安全值，允许被
`/刷新放送` 刷新；如果有"老手填值不应该被覆盖"的需求，跑一次 SQL 批量
回填：`UPDATE ... SET broadcast_manual=1 WHERE <识别条件>`。

### 3. Setter 联动（一次写入俩字段）

```python
def set_subject_broadcast_time(self, subject_id, broadcast_time, broadcast_weekday=None):
    subject = session.query(BangumiSubject).filter_by(subject_id=str(subject_id)).first()
    if not subject:
        return False
    subject.broadcast_time = broadcast_time
    if broadcast_weekday is not None:
        subject.broadcast_weekday = broadcast_weekday
    # ponytail: 手动设值 / 清空都同步锁定位。空值即未锁定(让 bgmlist 重新填充)。
    subject.broadcast_manual = broadcast_time is not None
    session.commit()
    return True
```

`broadcast_time is not None` 一行双写：设值→锁，清空→解。比让用户单独
`/解锁` 少一个命令。

### 4. 写入器底层守一道

```python
def batch_update_broadcast_times(self, mapping: dict) -> int:
    for subject in subjects:
        sid = subject.subject_id
        if sid not in mapping:
            continue
        # ponytail: 手动锁定的不动。让 /刷新放送 跳过用户手填的记录。
        if getattr(subject, "broadcast_manual", False):
            continue
        # ...写 time / weekday...
```

`getattr(..., False)` 而非 `subject.broadcast_manual`——migration 期间老行
可能缺列（False 兜底不抛 AttributeError），新代码也不会因 schema drift 崩。

**关键决策点：守在底层 writer 而非调用方**。`batch_update_broadcast_times`
是所有"自动写"的汇聚点；`_auto_fill_broadcast_times`、`/刷新放送`、未来
可能加的 `/从 bgmlist 拉取`、`/重新解析` 等都走它。**单点守一道覆盖全
调用方**，不需要每个调用方重复写 skip 逻辑。

### 5. UX：让用户知道手动状态

```python
# 查询时
locked = getattr(subject, "broadcast_manual", False)
lock_tag = "\n🔒 手动锁定,/刷新放送 不会覆盖" if locked else ""
yield f"📺 《{subject.name}》播出时间: {time}{lock_tag}"

# 清空时
yield "✅ 已清除播出时间设置\n已解除手动锁定,/刷新放送 将重新填充"
```

不告诉用户"为什么我手填的值没被刷掉"，他们会以为是 bug 然后去日志里查。

## 测试 recipe

stub `astrbot.api.logger`（repository 顶层 import 了它）：

```python
import sys, types
ab = types.ModuleType("astrbot"); abapi = types.ModuleType("astrbot.api")
class _L:
    def info(self,*a,**k): pass
    def error(self,*a,**k): pass
abapi.logger = _L()
sys.modules["astrbot"]=ab; sys.modules["astrbot.api"]=abapi
```

构造 3 行覆盖关键状态：
- `subject_id="A"`: 手动锁定（`manual=True`）
- `subject_id="B"`: 自动填充（`manual=False`, `time` 非空）
- `subject_id="C"`: 空（`manual=False`, `time=None`）

跑：
1. `set_*` → 断言 `manual` 翻转（True/False/True）
2. `batch_update({A: ..., B: ..., C: ...})` → 断言 A 没变、B 没变（非空跳过）、C 写入、`updated == 1`
3. `set_*(None)` → `manual=False` → 再 batch_update A → 写入成功

## 通用化检查清单

任何满足"用户可设值 + 系统自动同步"的字段都该有 `<field>_manual` 列：

| 字段 | 自动源 | 用户覆写理由 |
|---|---|---|
| `broadcast_time` | bgmlist API | bgmlist 给错 |
| `notification_template` | 默认模板 | 用户自定义 |
| `rate_limit` | 智能限速 | 用户硬设 |
| `preferred_server` | 测速选最优 | 用户钉死 |

命名一致：`<field>` + `_manual`，这样查询/过滤都能 `WHERE <field>_manual = true`
一行搞定。