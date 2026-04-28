#!/data/data/com.termux/files/usr/bin/bash
log() {
    echo "[$(date '+%H:%M:%S')] [$1] $2" >> "$LOG_FILE"
}
