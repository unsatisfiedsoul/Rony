#!/data/data/com.termux/files/usr/bin/bash
# --- Internal Loader ---
# This ensures the module can find the logger even when run as a sub-process
if ! declare -f log_info > /dev/null; then
    # Find the project root relative to this script
    MODULE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(dirname "$MODULE_DIR")"
    source "$PROJECT_ROOT/core/config.sh"
    source "$PROJECT_ROOT/core/logger.sh"
fi

execute() {
    target=$1
    log INFO "SMB enum"
    enum4linux-ng "$target" > "$OUTPUT_DIR/enum_$target.txt"
}
