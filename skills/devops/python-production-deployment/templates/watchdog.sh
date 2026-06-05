#!/bin/bash
# {{APP_NAME}} Watchdog — health check every 5 minutes
set -euo pipefail

SERVICE_NAME="{{APP_NAME}}"
PROCESS_NAME="{{PROCESS_NAME}}"
INSTALL_DIR="{{INSTALL_DIR}}"
LOG_TAG="watchdog"
DATA_DIR="{{DATA_DIR}}"

MEM_LIMIT_MB=200
DISK_LIMIT_PCT=90
STALL_SECONDS=300

log() {
    local level="$1"; shift
    echo "[$LOG_TAG] [$level] $*"
    logger -t "$LOG_TAG" -p "user.$level" "$*"
}

# 1. Process alive?
proc_count=$(pgrep -f "${PROCESS_NAME}" | wc -l)
if [ "$proc_count" -lt 1 ]; then
    log "err" "进程 ${PROCESS_NAME} 未运行，尝试重启..."
    systemctl restart "${SERVICE_NAME}" || exit 1
    sleep 3
    if pgrep -f "${PROCESS_NAME}" > /dev/null; then
        log "info" "进程已重新启动"
    else
        log "err" "重启后进程仍未运行，需要人工介入"
        exit 2
    fi
fi

# 2. Memory check
proc_pid=$(pgrep -f "${PROCESS_NAME}" | head -1)
if [ -n "$proc_pid" ]; then
    mem_kb=$(awk '/VmRSS/{print $2}' /proc/"$proc_pid"/status 2>/dev/null || echo 0)
    mem_mb=$(( mem_kb / 1024 ))
    if [ "$mem_mb" -gt "$MEM_LIMIT_MB" ]; then
        log "warn" "内存使用 ${mem_mb}MB，超过阈值 ${MEM_LIMIT_MB}MB"
    fi
fi

# 3. Disk check
disk_usage=$(df "$DATA_DIR" 2>/dev/null | awk 'NR==2 {print $5}' | tr -d '%' || echo 0)
if [ "$disk_usage" -ge "$DISK_LIMIT_PCT" ]; then
    log "warn" "磁盘使用率 ${disk_usage}%，超过阈值 ${DISK_LIMIT_PCT}%"
fi

# 4. Output staleness check
latest_file=$(find "$DATA_DIR" -type f 2>/dev/null | sort | tail -1)
if [ -n "$latest_file" ]; then
    now_ts=$(date +%s)
    file_ts=$(stat -c '%Y' "$latest_file")
    age=$(( now_ts - file_ts ))
    if [ "$age" -gt "$STALL_SECONDS" ]; then
        log "warn" "疑似卡死：最新文件已 ${age}秒 未更新（阈值 ${STALL_SECONDS}s），重启进程..."
        systemctl restart "${SERVICE_NAME}"
    fi
fi

# 5. Service status
if ! systemctl is-active --quiet "${SERVICE_NAME}"; then
    log "err" "服务状态异常，重启..."
    systemctl restart "${SERVICE_NAME}"
fi

log "info" "巡检完成"
exit 0
