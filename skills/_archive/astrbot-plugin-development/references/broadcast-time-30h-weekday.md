# broadcast_time + broadcast_weekday schema migration (30h 制周时间表)

## Scenario

User wants a weekly schedule display ("每周X 22:00 番剧名") with **deep-night
slots shown as 24-29h** to disambiguate the next-day rollover. Examples:

- "周四 24:28" — meaning the Friday 00:28 slot, attributed to Thursday's night slot
- "周日 26:08" — meaning the Monday 02:08 slot, attributed to Sunday's night slot

This pattern applies to any plugin whose display has **time + day that can cross
midnight**, where the underlying API only gives you one of them.

## Why it's tricky (and why calendar is the wrong source)

The data sources typically don't match:

| Source | Gives | Missing | Stability |
|--------|-------|---------|-----------|
| bgmlist / onair API `begin` field | HH:MM + ISO datetime (UTC+8) | weekday (derivable from datetime) | **stable** — GitHub Pages static JSON |
| bgmlist / onair API | HH:MM | weekday | (same as above) |
| BGM `/calendar` API | weekday | HH:MM | **unstable** — same subject returns different wid between fetches |
| AniDB / RSS | airdate (one-off) | recurring weekday | n/a |

**Empirical evidence (real session):** Two consecutive `/刷新放送` calls produced different weekday for the same subject (周三 → 周四). Root cause: BGM `/calendar` is a dynamic API whose result varies between calls even within minutes. Don't trust it for a stable weekday value.

**The right source:** `bgmlist.begin` is an ISO datetime string like `"2026-04-06T14:00:00.000Z"`. Convert to CST (`astimezone(UTC+8)`), then call `.isoweekday()` — gives 1-7 directly, stable across calls.

```python
def _parse_broadcast_time(begin_iso: str) -> tuple[str, int] | None:
    dt = datetime.datetime.fromisoformat(begin_iso.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.UTC)
    cst_dt = dt.astimezone(datetime.timezone(datetime.timedelta(hours=8)))
    return cst_dt.strftime("%H:%M"), cst_dt.isoweekday()
```

So your `_auto_fill` step should fetch weekday from `bgmlist.begin` (stable), not BGM `/calendar` (unstable).
"shows Thursday but user expected Friday" bugs.

## The 6-step migration (battle-tested)

When extending an existing schema, do NOT introduce Alembic. SQLite ALTER TABLE
+ SQLAlchemy ORM coexistence works fine if you do all 6:

### 1. ALTER TABLE the SQLite DB

```bash
sqlite3 data/plugin_data/<plugin>/data.db \
  "ALTER TABLE bangumi_subjects ADD COLUMN broadcast_weekday INTEGER;"
```

Direct ALTER. SQLAlchemy won't do this for you (it only creates new tables).

### 2. Add the ORM field

```python
# src/db/models.py
class BangumiSubject(Base):
    broadcast_time: Mapped[str | None] = mapped_column(String, nullable=True)
    broadcast_weekday: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # ISO weekday 1=周一..7=周日, paired with broadcast_time on every write
```

### 3. Extend the batch-update signature

Original signature took `dict[str, str]`. Now needs to accept tuple for atomic
time+weekday write:

```python
def batch_update_broadcast_times(
    self, mapping: dict[str, str | tuple[str, int | None]]
) -> int:
    ...
    for subject in subjects:
        value = mapping[sid]
        if isinstance(value, tuple):
            subject.broadcast_time, subject.broadcast_weekday = value
        else:
            subject.broadcast_time = value
```

Atomic write ensures they never drift apart.

### 4. Late-night shift in the auto-fill

```python
def _shift_late_night(hhmm: str, wid: int) -> tuple[str, int | None]:
    h, m = hhmm.split(":", 1)
    hh = int(h)
    if hh < 5 and wid > 0:  # 00:00-04:59 视为前一日档
        return f"{hh + 24:02d}:{m}", wid - 1 or 7  # wid 1-7 wrap to 7
    return hhmm, wid if wid else None
```

Apply during `_auto_fill_broadcast_times` after fetching calendar weekday.

### 5. Read-from-DB in display, NOT calendar

```python
# /放送时间 无参表格:
for s in subjects:
    wid = getattr(s, "broadcast_weekday", None) or 0
    bt = s.broadcast_time or ""
    # ...sort by (wid, time)...
```

**Do not** call `service.get_calendar()` here. Calendar has a cache, and
write-time vs display-time fetches may hit different cached snapshots → wid
mismatch → wrong day attribution.

### 6. SQL backfill when sandbox has no network

```bash
sqlite3 data.db "UPDATE bangumi_subjects SET broadcast_weekday=4,
  broadcast_time='24:28' WHERE subject_id='617123';"
```

Source the weekday from the **most recent user-visible screenshot/log** showing
the correct attribution. Update all rows in one transaction; verify with a
SELECT showing the expected sort order.

## Pitfalls

- **`time_pattern` regex must accept 24-29h** if users set times manually:
  ```python
  time_pattern = re.compile(r"^([01]\d|2[0-9]):([0-5]\d)$")  # was ([01]\d|2[0-3])
  ```
  Otherwise `/放送时间 <番剧> 24:28` is rejected as "格式错误".

- **`overwrite=False` skip logic must check BOTH time and weekday**:
  ```python
  if (not overwrite and subject.broadcast_time
      and getattr(subject, "broadcast_weekday", None)):
      continue  # skip only if both are set
  ```
  Otherwise an existing time without weekday never gets weekday filled.

- **Sort key: `(wid * 10000) + _time_to_min(bt)`** — the 10000 base puts 24:28
  (1448 min) on day 4 < 00:30 (30 min) on day 5, no special handling needed.

- **Triple-patch trap** (saw this in real session): when patching `entries.append(...)`
  that has multi-line parens, an old_string-only patch can leave dangling
  `entries.append(\n` artifacts. Re-read the file after patch; if the diff shows
  doubled `entries.append(` lines, that's the bug.

- **force-push + amend dance after CI failure**: amend fold working-tree
  changes into the commit **before** force-push, otherwise CI runs the old
  formatted commit while you think you pushed the new one.

## User signal patterns

- "还是有问题" after a fix = root cause missed. Re-trace data flow, not the
  display logic.
- "把 X 流程和我讲一遍" = literal trace request, not a fix request.
- "我建议你改一下" / "能不能实现 X" = wants feature; if X implies cross-day
  semantics, this is when you introduce weekday storage.
