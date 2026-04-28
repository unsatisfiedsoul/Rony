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
    local scavenge_file="$OUTPUT_DIR/scavenge_${target}.txt"
    
    log_info "Searching for sensitive files on: $target"

    # List of common sensitive files to check
    local paths=(".env" ".git/config" "robots.txt" "sitemap.xml" ".htaccess" "phpinfo.php")

    for path in "${paths[@]}"; do
        log_debug "Checking: /$path"
        # We use -L to follow redirects and --head to be fast
        local status=$(curl -kLs -o /dev/null -w "%{http_code}" -m 5 "http://$target/$path")
        
        if [[ "$status" == "200" ]]; then
            log_warn "FOUND: /$path (Status: 200)"
            echo "[FOUND] http://$target/$path" >> "$scavenge_file"
            
            # If it's a small text file like robots.txt or .env, let's grab the content
            if [[ "$path" == "robots.txt" || "$path" == ".env" ]]; then
                echo "--- Content of $path ---" >> "$scavenge_file"
                curl -kLs -m 5 "http://$target/$path" | head -n 20 >> "$scavenge_file"
                echo -e "\n-----------------------" >> "$scavenge_file"
            fi
        fi
    done

    if [[ -f "$scavenge_file" ]]; then
        log_info "Scavenging complete. Potential leaks saved to $scavenge_file"
    else
        log_info "No common sensitive files exposed."
    fi
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    execute "$1"
fi
