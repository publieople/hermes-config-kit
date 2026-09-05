#!/usr/bin/env bash
# 验证 AstrBot 插件是否真加载到 runtime
# 用法: verify_plugin.sh <plugin_name>  (e.g. astrbot_plugin_Pic)
# 返回 0 = 加载成功,1 = 失败

set -e
PLUGIN_NAME="${1:?usage: verify_plugin.sh <plugin_name>}"
SERVICE="${SERVICE:-astrbot}"

# 1. 确认文件存在
PLUGIN_DIR="$HOME/astrbot/data/plugins/$PLUGIN_NAME"
if [ ! -d "$PLUGIN_DIR" ]; then
  echo "FAIL: $PLUGIN_DIR 不存在"
  exit 1
fi

# 2. 重启服务
echo ">>> 重启 $SERVICE ..."
sudo systemctl restart "$SERVICE"
sleep 3

# 3. 看日志
echo ">>> 最近 1 分钟日志(过滤插件相关):"
if sudo journalctl -u "$SERVICE" --since "1 min ago" --no-pager 2>/dev/null | grep -iE "Loading plugin $PLUGIN_NAME|Added llm tool:|Plugin $PLUGIN_NAME" | tail -10; then
  :
else
  echo "FAIL: 日志里没找到插件加载记录"
  exit 1
fi

# 4. 检查是否有 error
echo ">>> 最近 1 分钟 error 记录:"
ERR_COUNT=$(sudo journalctl -u "$SERVICE" --since "1 min ago" --no-pager 2>/dev/null | grep -iE "error|exception|traceback" | grep -iE "$PLUGIN_NAME" | wc -l)
if [ "$ERR_COUNT" -gt 0 ]; then
  echo "WARN: 发现 $ERR_COUNT 条 error 记录(可能是预期的,人工核查)"
  sudo journalctl -u "$SERVICE" --since "1 min ago" --no-pager 2>/dev/null | grep -iE "error|exception|traceback" | grep -iE "$PLUGIN_NAME" | head -5
else
  echo "OK: 无 error"
fi

echo ""
echo ">>> 总结:插件 $PLUGIN_NAME 应该已加载"
