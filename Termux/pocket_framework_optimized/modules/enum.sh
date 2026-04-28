#!/data/data/com.termux/files/usr/bin/bash
execute() {
    target=$1
    log INFO "SMB enum"
    enum4linux-ng "$target" > "$OUTPUT_DIR/enum_$target.txt"
}
