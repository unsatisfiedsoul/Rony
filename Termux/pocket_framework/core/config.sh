#!/data/data/com.termux/files/usr/bin/bash

export PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
export MODULES_DIR="$PROJECT_ROOT/modules"
export LOG_DIR="$PROJECT_ROOT/logs"
export LOG_FILE="$LOG_DIR/framework.log"

# Function to set the target-specific directory
set_target_dir() {
    local target="$1"
    export TARGET_DIR="$PROJECT_ROOT/data/results/$target"
    mkdir -p "$TARGET_DIR"
    # Update OUTPUT_DIR for the modules to use
    export OUTPUT_DIR="$TARGET_DIR"
}

mkdir -p "$LOG_DIR"
