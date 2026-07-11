# ComfyUI 服务端诊断 recipe

排查 AstrBot → ComfyUI 链路故障时，**用这些命令在 5 分钟内定位是哪一截挂了**。

## 1. 三层怀疑对象 + 顺序

| 层 | 怀疑 | 验证方式 |
|---|---|---|
| 服务端 | ComfyUI 没活 / 模型错 / 节点错 | `curl /system_stats` + `journalctl -u comfyui` + `/history/{pid}` |
| 桥接层 | promax 解析错 / 配置错 / 翻译没开 | `data/config/astrbot_plugin_ComfyUI_promax_config.json` + `_inject_user_params` 源码 |
| 客户端 | AstrBot 日志死路 / 消息没发到群 | `journalctl --user -u astrbot` + QQ 群实际表现 |

**默认从服务端开始**。如果 `/history/{pid}` 里 node 11 的 text 字段是用户原话（甚至带 MSG_ID），就**直接证明桥接层工作了**，剩下只有客户端配置问题。

## 2. ComfyUI 端点速查

| 端点 | 用途 | 注意事项 |
|---|---|---|
| `GET /` | 前端 HTML | 通 = 进程活 |
| `GET /system_stats` | 资源使用 | 健康检查用 |
| `GET /object_info` | 2295+ 节点 schema | 查 CLIPLoader type 字段可选值 |
| `GET /models/checkpoints` | 列出 checkpoint | 看 Anima 等模型是否被识别 |
| `GET /models/text_encoders` | 列出文本编码器 | Anima 走 `qwen_3_06b_base.safetensors` |
| `GET /queue` | 当前 running + pending | 看是否有任务堆积 |
| `GET /history?max_items=N` | 历史（**truncated**） | prompt 字段被 `[truncated]` 替换，**不能用** |
| `GET /history/{prompt_id}` | 单条历史（**完整**） | **诊断唯一可靠入口** |

## 3. 完整诊断脚本

```bash
# 假设本地端口转发 127.0.0.1:8188 已通

# A. 服务活
curl -s -o /dev/null -w "comfyui root: %{http_code}\n" http://127.0.0.1:8188/

# B. 最近 5 条任务在服务器上的执行情况
ssh -i ~/.ssh/id_ed25519 -p <port> user@host \
  "sudo -n journalctl -u comfyui -n 100 --no-pager | grep -E 'got prompt|Prompt executed|Error|Traceback' | tail -20"

# C. 取最近一次成功的 prompt_id，导出完整 prompt JSON
PID=$(curl -s "http://127.0.0.1:8188/history?max_items=1" | \
      python3 -c "import sys,json; print(list(json.load(sys.stdin).keys())[0])")
echo "prompt_id: $PID"
curl -s "http://127.0.0.1:8188/history/$PID" | \
  python3 -c "
import sys, json
d = json.load(sys.stdin)
for pid, item in d.items():
    pj = item['prompt'][2]
    for nid, nd in pj.items():
        if nd.get('class_type') == 'CLIPTextEncode':
            text = nd.get('inputs', {}).get('text', '<missing>')
            print(f'  node {nid} text: {text!r}'[:200])
"

# D. 检查 GPU 占用
ssh user@host "nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader | head -4"

# E. 看 output 目录的最新出图
ssh user@host "ls -lt /data/comfy/ComfyUI/output/*.png 2>/dev/null | head -5"
```

## 4. 真实错误样例库

### 4.1 "KeyError: 'prompt'" — comfyui-impact-pack bug（无害）

```
[Impact Pack] ComfyUI-Error on prompt - several features will not work.
KeyError: 'prompt'
  File ".../comfyui-impact-pack/modules/impact/impact_server.py", line 573
  File ".../comfyui-inspire-pack/inspire/inspire_server.py", line 255
```

**根因**：Impact Pack / Inspire Pack 的 on_prompt_handler 假定新格式 payload，但 promax 发的 `prompt` 字段结构不对。**但 ComfyUI 主体执行仍然成功**，图照样出。**忽略即可**——是 impact_pack 自己的兼容性问题。

### 4.2 Anima + `qwen_3_06b_base` + `type=stable_diffusion` — **正确配法**

很多帖子里说应该改成 `type=qwen_image` 或别的，**实际不需要**。Anima 模型权重里自己内嵌了 Qwen3 兼容层，promax 跑 8 次都成功，32 秒一张图。**换 CLIP 模型 = 出鬼画符**。

### 4.3 中文 prompt 出图不对应

`enable_translation: false` 时 promax 把中文原样塞进 node 11 text：

```json
"11": {"inputs": {"text": "抽烟的白毛猫娘 [MSG_ID:327601470]"}}
```

Qwen3 0.6B 切中文 token 出乱码 ids，ComfyUI 出图质量差 / 内容不对应。**修法**：

1. `enable_translation: true`（调 LLM 翻成 Danbooru 英文标签）
2. 或用户**直接发英文 Danbooru 标签**（最高效）：
   ```
   anima 1girl, white_hair, cat_girl, smoking, cigarette
   ```

### 4.4 用户没收到图（最隐蔽）

`/history/{pid}` 显示图生成成功，output 目录有图，**但群里没收到**。原因按概率排：

1. `enable_fake_forward: true` + `fake_forward_qq: ""` — 转发失败
2. `enable_auto_recall: true` + `auto_recall_delay: 20` — 图发出去 20 秒后撤回了
3. `daily_download_limit: 1` — 当天超限
4. `group_whitelist` 没配用户群
5. AstrBot 日志死路（`log_file_enable: false` + systemd 拉起）— 没法事后排查

## 5. AstrBot v4 配置位置速查

| 内容 | 路径 |
|---|---|
| 主配置 | `data/cmd_config.json`（顶层 AstrBot 全局） |
| 插件配置 | `data/config/astrbot_plugin_<plugin>_config.json` |
| 插件数据 | `data/plugin_data/astrbot_plugin_<plugin>/` |
| 工作流定义 | `data/plugins/astrbot_plugin_ComfyUI_promax/workflow/<name>.json` |
| 工作流配置 | `data/plugins/astrbot_plugin_ComfyUI_promax/data/output/workflows/<name>/config.json` |
| 日志（死路） | `data/astrbot.log`（默认不写，看 journalctl） |

promax 的 `aimg` 走内置 `_build_comfyui_prompt`，**`anima` / `encrypt` / 自定义前缀**走 `_inject_user_params` (workflow 模式)。两种路径的 prompt 注入逻辑不一样，调试时要看清是哪个。

## 6. 提示词注入的"反直觉点"

读 `main.py:1130-1200` `handle_workflow`：

- 用户发 `anima 抽烟的白毛猫娘` → `words[0]="anima"`, `params_text="抽烟的白毛猫娘"`
- `params_text` 按 `key:value` 模式切分 → 没有这种模式 → 整段进 `prompt_parts`
- `prompt_text` 有中文 → 调 `_translate_cn_prompt` 走 LLM 翻译
- `args = ["提示词:<翻译结果>"]`
- `build_workflow` 按 `node_id:param_name` 查表（11:text）→ 注入

**所以"提示词没生效"的根因排查顺序**：

1. `_translate_cn_prompt` 返回空？→ LLM provider 配错 / context.get_using_provider() 拿到空
2. `build_workflow` 的 key 拼不上？→ `config.json` 里 `node_configs` 字段名写错 / aliases 漏配
3. ComfyUI 端没收到？→ 看 `/history/{pid}` 的 node 11 text 字段
