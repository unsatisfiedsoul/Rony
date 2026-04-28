#!/data/data/com.termux/files/usr/bin/bash

# This module performs the primary port scan.
# The output is parsed by core/decision.sh to trigger service-specific modules.

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
    local target="$1"
    local scan_file="$OUTPUT_DIR/scan_${target}.txt"

    log_info "Initiating Service Discovery Scan on: $target"

    # 1. Prep Environment
    mkdir -p "$OUTPUT_DIR"

    # 2. Execution
    # -sV: Probe open ports to determine service/version info
    # -T4: Faster execution (suitable for most modern networks)
    # --open: Only show open ports (makes Decision.sh parsing faster)
    # --max-retries 1: Prevents Nmap from wasting time on unstable packets
    log_debug "Running Nmap service scan..."
    
    if nmap -sV -T4 --open --max-retries 1 "$target" -oN "$scan_file" > /dev/null; then
        
        # 3. Quick Check for Results
        if grep -q "open" "$scan_file"; then
            local port_count
            port_count=$(grep -c "open" "$scan_file")
            log_info "Scan complete. Found $port_count open ports."
        else
            log_warn "Scan complete, but no open ports were found on $target."
        fi
        return 0
    else
        log_error "Nmap scan encountered an error for $target."
        return 1
    fi
}

# Standalone execution support
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    # Ensure config and logger are sourced if run manually
    source "$(dirname "$0")/../core/config.sh"
    source "$(dirname "$0")/../core/logger.sh"
    execute "$1"
fi
