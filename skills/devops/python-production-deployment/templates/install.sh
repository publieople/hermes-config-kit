#!/bin/bash
# {{APP_NAME}} 一键部署脚本
set -euo pipefail

INSTALL_DIR="{{INSTALL_DIR}}"
DATA_DIR="{{DATA_DIR}}"
DEFAULT_SERVER="${1:-192.168.1.100}"

if [ "$(id -u)" -ne 0 ]; then
    echo "错误：请使用 sudo 运行"
    exit 1
fi

echo "================================================"
echo "  {{APP_NAME}} 部署脚本"
echo "================================================"
echo "目标目录: ${INSTALL_DIR}"
echo "数据目录: ${DATA_DIR}"
echo "服务器 IP: ${DEFAULT_SERVER}"
echo ""

# Create directories
mkdir -p "${INSTALL_DIR}/deploy" "${DATA_DIR}"

# Copy source code
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC_DIR="$(dirname "$SCRIPT_DIR")"
cp "${SRC_DIR}"/*.py "${INSTALL_DIR}/" 2>/dev/null || true
chmod 755 "${INSTALL_DIR}"/*.py

# Write env config
cat > "${INSTALL_DIR}/{{APP_NAME}}.env" << EOF
# {{APP_NAME}} 配置
SERVER_IP=${DEFAULT_SERVER}
SERVER_PORT=8888
DURATION=60
INTERVAL=1
OUTPUT_DIR=${DATA_DIR}
EOF

# Copy deploy files
cp "${SCRIPT_DIR}/{{APP_NAME}}.service" /etc/systemd/system/
cp "${SCRIPT_DIR}/watchdog.sh" "${INSTALL_DIR}/deploy/"
chmod 755 "${INSTALL_DIR}/deploy/watchdog.sh"

# Install systemd service
systemctl daemon-reload
systemctl enable "{{APP_NAME}}.service"
echo ">>> systemd 服务已安装（开机自启）"

# Install watchdog cron
cat > /etc/cron.d/{{APP_NAME}}-watchdog << 'CRONEOF'
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
*/5 * * * * root /opt/{{APP_NAME}}/deploy/watchdog.sh > /dev/null 2>&1
CRONEOF
chmod 644 /etc/cron.d/{{APP_NAME}}-watchdog
echo ">>> Watchdog cron 已安装"

echo ""
echo "================================================"
echo "  部署完成！"
echo "================================================"
echo ""
echo "启动服务:  sudo systemctl start {{APP_NAME}}"
echo "查看日志:  journalctl -u {{APP_NAME}} -f"
echo "测试看门狗: sudo ${INSTALL_DIR}/deploy/watchdog.sh"
