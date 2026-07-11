# Self-evolving AstrBot skill pattern

通用模式 — 让 AstrBot 的 LLM 学会调任意一个外部工具,工具演进了不用人手动重写 skill。

## 何时用这模式

- 工具有不断扩展的 API surface(ComfyUI 的新模型/节点、外部 SaaS 增版本)
- 用户嫌"每次升级都得改插件"
- 工具的"调用范式"是**相对稳定**的(都是 HTTP/CLI/SQL/...) — 演化的是 payload,不是 transport
- 不需要发给别人用(自己/小团队内部)
- 工作流/查询模板数量有限(<10), 用户能维护 json/yaml 文件

不适用:
- 调用范式本身就变(API 协议完全不同)
- 需要给别人用的产品级功能
- 工具只调一次,技能没有"演化"价值

## 文件结构

全部放 AstrBot 数据目录,**不污染 skill 本身**:

```
# 1. Skill(教 LLM 通用范式, 不绑死任何具体调用)
data/skills/<slug>/
  SKILL.md              # < 200 行, 只讲通用调用范式 + 演化机制
  _meta.json

# 2. 工作流/查询模板(用户/Agent 自己维护)
data/<slug>_workflows/<name>/
  <file>.json|.yaml     # 实际的工作流/查询/SQL/pipeline 定义
  README.md             # 何时用, 入口节点 ID/参数表, 输出格式 (3-10 行)

# 3. 评估集(回归测试, 防演化变渣)
data/<slug>_eval/
  <workflow>.md         # 该工作流下 3-5 个代表性 prompt + 期望行为

# 4. 训练数据(LLM 跑的轨迹, 演化引擎的输入)
data/<slug>_journal/
  YYYY-MM-DD-N.md       # 每次跑完追加: prompt / 选哪个 workflow / 结果 / 学到的事
```

**关键**: `data/<slug>_workflows/` 必须跟 `data/<slug>_eval/` 和 `data/<slug>_journal/` 在同一树。LLM `ls` 就能扫到, 不需要任何注册/索引步骤。

## SKILL.md 必须包含的 4 段

1. **何时调用**(trigger) — description 字段写满触发词, LLM 按它做 trigger 匹配(非按 skill 名)
2. **通用调用范式** — 该工具的"骨架接口", 例如 ComfyUI 是 5 步 (object_info → load wf → POST /prompt → poll → /view), SQL 是 connect → query → fetchall → close
3. **payload 怎么挑** — 教 LLM "看 data/<slug>_workflows/ 下的 README 决定 payload / 节点 ID / 参数", **不写死在 SKILL.md 里**
4. **演化机制** — 触发条件 + patch 流程 + 评估集门控 + journal 追加(见下)

## Journal 条目 schema

每次跑完生图/调用, LLM **必须**追加一条:

```markdown
# <任务简述>

- 时间: <ISO>
- 用户原文: ...
- 选的工作流: <name>
  - 理由: ...
- payload: ...                 # 实际注入的参数
- 结果: success / error + 出图路径或 error 信息
- 学到的 (下一步要改的事):
  - 1. ...
  - 2. ...
```

**"学到的"是关键** — 不是日志, 是训练数据, 演化引擎从这里挖信号。

## 演化循环

触发条件(任一满足就跑):

1. `data/<slug>_journal/` 累积 ≥ 5 条
2. 同一类 prompt 连续失败 ≥ 2 次
3. 用户显式说 "这 skill 总是 XXX 不行"

执行步骤(LLM 自己跑, 无框架):

```
1. 收集证据
   - 读全部 journal
   - 读当前 SKILL.md
   - 读全部 eval/<workflow>.md

2. 总结"老 SKILL.md 哪条反复被打脸"
   - 哪段流程同类型任务至少 2 次出错过?
   - 哪类用户 prompt SKILL.md 完全没覆盖?

3. 提 patch (严格只用 add/delete/replace)
   DEL: 原句
   ADD: 新句
   REP: 原句 → 新句
   - 每次 patch < 当前 SKILL.md 的 20% (避免整段重写导致回归)

4. 备份当前 SKILL.md
   cp SKILL.md .archive/<timestamp>/SKILL.md

5. Held-out 门控
   - 对每个 eval/<workflow>.md 跑一遍生成
   - 全部通过 → 接 patch, 落地
   - 任一回归 → 拒绝, journal 加一条 "patch rejected: <原因>"

6. 评估集持续生长
   接 patch 后, 主动给对应 eval 加一条新 case (把本次回归原因固化成测试)
   不让同一个 bug 再犯
```

## SkillOpt 对照(为什么不要装 SkillOpt)

| SkillOpt 有 | 这模式用什么替代 |
|---|---|
| Rollout → Reflect → Edit → Validate | LLM 自己读 journal + run eval |
| Optimizer model | LLM 自身就是 optimizer |
| Held-out validation gate | `data/<slug>_eval/<name>.md` |
| Rejected-edit buffer | journal 里 "patch rejected" 条目 |
| Epoch / batch | journal 累积触发 |
| WebUI 仪表盘 | `ls data/<slug>_journal/ \| wc -l` 就够 |
| 多模型 backend | LLM 自身 |
| 6 个 benchmark | 你自己的 eval/ 目录, 一次补一条 |

**最重要的差异**: SkillOpt 是 "训练一个独立 artifact 然后部署", 这模式是 "SKILL.md 就是训练状态本身", **零训练-部署 gap**。

## 反模式(常见的写错方式)

- 把"何时调用"写得含糊 → LLM 不调用这个 skill, 调用了别的插件/路径
- SKILL.md 写得太长(>300 行) → 加载它吃掉 context, LLM 不会认真读完
- Journal 缺"学到的"字段 → 演化引擎没数据可用, 退化到 "随机 patch"
- Eval prompt 太特殊化 → 任何改动都回归, 演化锁死
- 每次只重写 SKILL.md 不更新 eval → 没法证明新版本比旧版本好

## 适用/不适用 case 总览

适合:
- ComfyUI (Anima/Flux/Wan2.2/未来模型)
- Git (LLM 学各种 repo 维护操作)
- ffmpeg (LLM 学如何组合视频转换 pipeline)
- SQL (LLM 学特定 schema 的查询模板)
- 任意外部 SaaS API (Notion/GitHub/Google Workspace 高级查询)

不适合:
- 单一固定 API 调用次数极少(不值得搞演化机制)
- 要求别人也能用的产品级功能(发 plugin marketplace, 别走这条)
- 工具的"调用范式"本身就常变(协议级变化, 不是参数级)

## 首次铺底 checklist

建一个新 self-evolve skill 要做的事:

1. 写 SKILL.md + _meta.json (内容看上面 4 段)
2. mkdir data/<slug>_{workflows,eval,journal}
3. 让用户准备第一个工作流 JSON + 写 README
4. 你 (agent) 帮用户手写 eval/<workflow>.md 的前 3 条
5. AstrBot WebUI 重载 skills
6. 跑一次 — journal 自动开始累积
7. (可选) 让 LLM 跑一遍假装演化, 验证机制能运转
