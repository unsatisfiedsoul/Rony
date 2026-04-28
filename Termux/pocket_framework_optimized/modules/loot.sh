#!/data/data/com.termux/files/usr/bin/bash
execute() {
    log INFO "Loot"
    grep -rnE "password|token" "$OUTPUT_DIR" > "$OUTPUT_DIR/loot.txt"
}
