#!/data/data/com.termux/files/usr/bin/bash

execute() {
    local target="$1"
    local sub_file="$OUTPUT_DIR/subdomains_${target}.txt"
    local live_file="$OUTPUT_DIR/live_subs_${target}.txt"
    
    log_info "Running Subfinder on: $target"
    subfinder -d "$target" -silent -o "$sub_file"

    if [[ -s "$sub_file" ]]; then
        log_info "Probing for live subdomains with HTTPX..."
        # httpx checks which subdomains actually respond to web requests
        cat "$sub_file" | httpx -silent -mc 200,301,302 -o "$live_file"
        log_info "Found $(wc -l < "$live_file") live subdomains."
    else
        log_error "Subfinder returned no results."
    fi
}
