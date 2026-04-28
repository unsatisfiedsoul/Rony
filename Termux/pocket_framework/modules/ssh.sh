#!/data/data/com.termux/files/usr/bin/bash

# This module performs SSH service enumeration.
# It identifies the SSH version and retrieves host keys for the final report.

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
    local ssh_file="$OUTPUT_DIR/ssh_${target}.txt"
    
    log_info "Starting SSH Enumeration on: $target"

    # 1. Dependency Check
    if ! command -v nc &> /dev/null || ! command -v ssh-keyscan &> /dev/null; then
        log_error "Missing dependencies: ensure 'netcat-openbsd' and 'openssh' are installed."
        return 1
    fi

    # 2. Banner Grabbing (Identification)
    # We use netcat to grab the first line the server sends
    log_debug "Attempting to grab SSH banner..."
    local banner
    banner=$(echo "EXIT" | nc -w 5 "$target" 22 | head -n 1 | tr -d '\r')
    
    if [[ -n "$banner" ]]; then
        log_info "SSH Banner: $banner"
        echo "Banner: $banner" > "$ssh_file"
    else
        log_warn "Could not retrieve SSH banner from $target."
        echo "Banner: Unknown" > "$ssh_file"
    fi

    # 3. Host Key Extraction
    # -t: specify key types, -p: port
    log_debug "Retrieving public host keys..."
    echo -e "\n[ Host Keys ]" >> "$ssh_file"
    ssh-keyscan -t rsa,ed25519 -p 22 "$target" 2>/dev/null >> "$ssh_file"

    # 4. Feature Audit (Optional but useful)
    # This checks if the server supports older, weaker algorithms
    log_debug "Auditing supported algorithms..."
    echo -e "\n[ Supported Algorithms ]" >> "$ssh_file"
    # We use ssh -G to see how the client would connect to this target
    ssh -o "BatchMode=yes" -o "ConnectTimeout=5" -G "$target" | grep -E "kex|ciphers|macs" >> "$ssh_file"

    log_info "SSH enumeration for $target complete."
    return 0
}

# Standalone execution support
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    source "$(dirname "$0")/../core/config.sh"
    source "$(dirname "$0")/../core/logger.sh"
    execute "$1"
fi
