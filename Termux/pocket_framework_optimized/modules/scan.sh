#!/data/data/com.termux/files/usr/bin/bash
execute() {
    target=$1
    log INFO "Fast scan"
    nmap -T3 -F "$target" -oN "$OUTPUT_DIR/scan_$target.txt"
}
