# SKILL.md 编写坑 — 写"通用 ComfyUI skill"时第一次跑通撞到的

记 2026-07-09 端到端冒烟时发现的 5 个错。**下一个写 ComfyUI 类 SKILL.md 的人应该先读这页**,别重蹈。

---

## 坑 1: 示例全用 `jq`,系统没装

AstrBot 跑在 `uv tool`(非开发机),`jq` **不在 PATH**。

**症状**: SKILL.md 里所有 `| jq '.foo'` 的示例,LLM 跟着写,卡在 `command not found`,然后 LLM 会退化到乱写 Python json 解析。

**修法**: SKILL.md 默认走 Python,json 是 stdlib,uv tool AstrBot 必有:

```bash
# 列所有节点
curl -s http://127.0.0.1:8188/object_info | python3 -c "import json,sys; print(list(json.load(sys.stdin).keys()))"

# 查一个节点的输入 schema
curl -s http://127.0.0.1:8188/object_info/CLIPTextEncode | python3 -c "import json,sys; print(list(json.load(sys.stdin)['input']['required'].keys()))"
```

如果一定要 `jq`,写明 "**需先 `apt install jq` 或 `pip install yq`**"。

---

## 坑 2: 取图硬编码 SaveImage 节点 ID

**症状**: 别人的 workflow 里 SaveImage 节点 ID 不一定是 `46`,硬编码 `outputs["46"]` 在新 workflow 上直接 KeyError。

**修法**: 遍历 outputs 取第一个有 images 的节点:

```bash
filename=$(PID_VAR="$prompt_id" python3 -c '
import json, os, urllib.request
pid = os.environ["PID_VAR"]
data = json.loads(urllib.request.urlopen(f"http://127.0.0.1:8188/history/{pid}", timeout=5).read())
for nid, n in data.get(pid, {}).get("outputs", {}).items():
    if n.get("images"):
        print(n["images"][0]["filename"]); break
')
```

跟 workflow 解耦,任意 workflow 都能取到图。

---

## 坑 3: polling `/history` 500 不报错会"卡死循环"

**症状**: 任务刚提交时,ComfyUI 端 history 偶尔 500(任务还没在 history 里)。LLM 写的 polling 没 try/except,exit code 0 但 status 永远是 "err",看起来任务完成了实际没拿到结果。

**修法**: polling 必须 try `urllib.error.HTTPError`,把 5xx 视为"queued"继续等:

```python
try:
    data = json.loads(urllib.request.urlopen(f".../history/{pid}", timeout=5).read())
    print(data.get(pid, {}).get("status", {}).get("status_str", "unknown"))
except urllib.error.HTTPError:
    print("queued")  # 任务还没落地,继续等
except Exception as e:
    print(f"err:{type(e).__name__}")
```

外壳用 `case "$status" in success|error) break ;; esac`,60s 超时再报错。

---

## 坑 4: `/object_info/<node>` 经常 `input.required` 为空

**症状**: LLM 看到 `CLIPTextEncode` 的 `/object_info` 字段是 `[]`,以为 schema 出了问题,或者反过来,把 schema 当真理之源,而 workflow 里的实际节点连线跟 schema 不一致。

**修法**: SKILL.md 里说清楚:

- `workflow_api.json` + 用户手写的 `README.md` 才是真理之源(节点 ID / 哪个节点接 prompt)
- `/object_info` 只用于"我不确定的节点 / 还没选 workflow 时"探索
- schema 为空 ≠ 节点不接受参数,可能是 hidden / optional

---

## 坑 5: `POST /prompt` 响应里的 `number` 字段不看

**症状**: 用户群被排队 30 多人卡到第 31 位,32-50 秒后才开始跑。LLM 默认 polling 32 秒,实际只完成半个任务 — 出图给用户后他以为"挺快",其实服务器已经忙到 OOM。

**修法**: SKILL.md 把 `number`(队列位置)写进 POST 响应说明,告知用户 "前面有 N 个任务":

```json
{"prompt_id": "...uuid...", "number": 31, "node_errors": {}}
```

`number > 10` 时告诉用户"前面 N 个任务,等待会拉长"。`node_errors` 非空时**直接换 workflow**,不报修。

---

## 验证过的端到端配置

本次真跑通过的最小 setup:

```
/home/po/astrbot/data/
  skills/comfyui/
    SKILL.md                              # 主 skill,跟上面 5 个坑对应已修
    _meta.json                            # ownerId+slug+version+publishedAt
  comfyui_workflows/anima_t2i/
    workflow_api.json                     # ComfyUI UI "Export (API Format)" 出
    README.md                             # 用户手写:何时用 / prompt 节点 ID / 推荐参数
  comfyui_journal/YYYY-MM-DD-NN.md        # 每次跑完追加
  comfyui_eval/anima_t2i.md               # 5 条回归 case
```

ComfyUI: 0.21.0,A10,22GB VRAM。SSH 隧道 `127.0.0.1:8188` 活着。
Anima 2B + Qwen3 0.6B 出图时长 32-50 秒,512x512 / 920x1536 都 OK。

---

## 自检清单(写完 SKILL.md 后跑一遍)

1. ✅ 所有 `jq` 换 `python3 -c`?
2. ✅ 取图是遍历 `outputs.*.images` 不是硬编码?
3. ✅ polling 有 `try/except urllib.error.HTTPError`?
4. ✅ README.md > object_info 这件事说清楚了?
5. ✅ POST 响应里的 `number` 字段提了?

**没做完第一遍测试不许发到 AstrBot 群里。**
