#!/data/data/com.termux/files/usr/bin/bash

execute() {
    local target="$1"

    # 1. Subdomain & Live Probing
    run_module "subdomain" "$target"

    # 2. Vulnerability Scanning (only if live subs exist)
    if [[ -s "$OUTPUT_DIR/live_subs_${target}.txt" ]]; then
        run_module "vulnerability" "$target"
    fi

    # 3. Standard Web/Scavenger on the main target
    run_module "web" "$target"
    run_module "scavenger" "$target"
}
