#!/data/data/com.termux/files/usr/bin/bash
execute() {
    target=$1
    log INFO "Web check"
    curl -I "$target" > "$OUTPUT_DIR/web_$target.txt"
}
