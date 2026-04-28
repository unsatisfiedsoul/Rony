#!/data/data/com.termux/files/usr/bin/bash

# --- Internal Loader ---
if ! declare -f log_info > /dev/null; then
    MODULE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(dirname "$MODULE_DIR")"
    source "$PROJECT_ROOT/core/config.sh"
    source "$PROJECT_ROOT/core/logger.sh"
fi

execute() {
    local target="$1"
    local web_file="$OUTPUT_DIR/web_${target}.txt"
    
    log_info "Starting Aggressive Web Enumeration on: $target"

    # AGGRESSIVE CURL FLAGS:
    # -k: Insecure (Ignore SSL errors)
    # -L: Follow redirects
    # -A: User-Agent (Look like Chrome on Windows)
    # -sI: Silent, Fetch Headers only
    # --connect-timeout: Don't hang forever
    curl -kLsI -m 15 -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36" \
         "http://$target" > "$web_file" 2>&1

    # Check if we actually got data
    if [[ ! -s "$web_file" ]]; then
        log_warn "HTTP failed, trying HTTPS specifically..."
        curl -kLsI -m 15 -A "Mozilla/5.0" "https://$target" > "$web_file" 2>&1
    fi

    if [[ -s "$web_file" ]]; then
        # Strip Windows line endings (\r) immediately
        sed -i 's/\r//g' "$web_file"
        
        local status=$(head -n 1 "$web_file" | awk '{print $2}')
        log_info "Web service responded with Status: $status"
    else
        log_error "Target $target refused all connections."
    fi
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    execute "$1"
fi
