#!/data/data/com.termux/files/usr/bin/bash

# This module performs SMB enumeration to identify Windows versions and shares.
# Triggered by port 445/139 detection in Decision.sh.

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
    local smb_file="$OUTPUT_DIR/smb_${target}.txt"
    
    log_info "Starting SMB Enumeration on: $target"

    # 1. Dependency Check
    if ! command -v nmap &> /dev/null; then
        log_error "Nmap is required for SMB scripts. Run 'pkg install nmap'."
        return 1
    fi

    # 2. OS and Domain Discovery
    # We use specific Nmap scripts for high-accuracy OS detection
    log_debug "Discovering SMB OS details..."
    echo "--- OS Discovery ---" > "$smb_file"
    nmap -p 445 --script smb-os-discovery "$target" | grep -E "OS:|Computer name:|Domain name:" >> "$smb_file"

    # 3. Share Enumeration (Guest/Anonymous)
    # Checks if we can see folders without a login
    log_debug "Checking for anonymous shares..."
    echo -e "\n--- Share Listing ---" >> "$smb_file"
    nmap -p 445 --script smb-enum-shares "$target" >> "$smb_file"

    # 4. Security Check (Samba versions / Guest access)
    if grep -q "Anonymous access: Allowed" "$smb_file"; then
        log_warn "SENSITIVE: Anonymous SMB access allowed on $target!"
        echo "ALERT: Anonymous access allowed" >> "$smb_file"
    fi

    # 5. Extract Computer Name for Logs
    local computer_name
    computer_name=$(grep "Computer name:" "$smb_file" | awk '{print $NF}')
    if [[ -n "$computer_name" ]]; then
        log_info "Target NetBIOS Name: $computer_name"
    fi

    log_info "SMB enumeration for $target complete."
    return 0
}

# Standalone execution support
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    source "$(dirname "$0")/../core/config.sh"
    source "$(dirname "$0")/../core/logger.sh"
    execute "$1"
fi
