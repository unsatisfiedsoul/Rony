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
    local target="$1"
    local recon_file="$OUTPUT_DIR/recon_${target}.txt"

    log_info "Starting Discovery Recon on: $target"

    if ! command -v nmap &> /dev/null; then
        log_error "Nmap is not installed."
        return 1
    fi

    log_debug "Running ping sweep..."
    if nmap -sn -T4 --host-timeout 2m "$target" -oN "$recon_file" > /dev/null; then
        if grep -q "Host is up" "$recon_file"; then
            log_info "Target $target is UP."
            return 0
        else
            log_warn "Target $target appears to be DOWN."
            return 1 # Return error so pipeline stops if target is dead
        fi
    else
        log_error "Nmap discovery failed."
        return 1
    fi
}

# This part handles the "bash modules/recon.sh target" execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    execute "$1"
fi
