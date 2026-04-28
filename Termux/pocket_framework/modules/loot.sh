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
    local final_report="$OUTPUT_DIR/SUMMARY_${target}.txt"
    local loot_file="$OUTPUT_DIR/LOOT_${target}.txt"

    log_info "Finalizing Results for: $target"

    # 1. Initialize SUMMARY
    {
        echo "==============================================="
        echo "      SECURITY SCAN SUMMARY: $target"
        echo "      Generated: $(date)"
        echo "==============================================="
        echo -e "\n[+] TARGET INFRASTRUCTURE"
    } > "$final_report"

    # 2. Infra & Services
    [[ -f "$OUTPUT_DIR/recon_${target}.txt" ]] && grep "Host is up" "$OUTPUT_DIR/recon_${target}.txt" >> "$final_report"
    echo -e "\n[+] DISCOVERED SERVICES" >> "$final_report"
    [[ -f "$OUTPUT_DIR/scan_${target}.txt" ]] && grep "open" "$OUTPUT_DIR/scan_${target}.txt" | sed "s/\r//g" >> "$final_report"

    # 2.5 Subdomain Discovery
    echo -e "\n[+] DISCOVERED SUBDOMAINS" >> "$final_report"
    if [[ -f "$OUTPUT_DIR/subdomains_${target}.txt" ]]; then
        cat "$OUTPUT_DIR/subdomains_${target}.txt" >> "$final_report"
    else
        echo "No subdomains discovered." >> "$final_report"
    fi


    # 3. Software Stack (Now includes Service Names)
    echo -e "\n[+] SOFTWARE & INFRASTRUCTURE" >> "$final_report"
    grep -rhEi "Server:|x-powered-by:|via:|x-nextjs-cache:" "$OUTPUT_DIR" --exclude="SUMMARY_*" --exclude="LOOT_*" 2>/dev/null | \
        sed -E "s/\\\\x20/ /g; s/\\\\r\\\\n/ /g; s/SF:[^ ]* //g; s/SF://g; s/[[:space:]]+/ /g; s/\r//g" | sort -u >> "$final_report"
    if [[ -f "$OUTPUT_DIR/scan_${target}.txt" ]]; then
        grep "open" "$OUTPUT_DIR/scan_${target}.txt" | awk '{for(i=4;i<=NF;i++) printf $i" "; print ""}' | sed 's/^[ \t]*//;s/[ \t]*$//' | sort -u >> "$final_report"
    fi

    # 4. Scavenged Paths
    echo -e "\n[+] EXPOSED FILES & PATHS" >> "$final_report"
    if [[ -f "$OUTPUT_DIR/scavenge_${target}.txt" ]]; then
        grep "\[FOUND\]" "$OUTPUT_DIR/scavenge_${target}.txt" >> "$final_report"
    else
        echo "No common sensitive paths detected." >> "$final_report"
    fi

    # 5. THE DEEP LOOT (Secrets/Cookies/Sensitive Strings)
    log_debug "Extracting sensitive data from all modules..."
    {
        echo "==============================================="
        echo "           EXTRACTED SENSITIVE DATA            "
        echo "==============================================="
    } > "$loot_file"

    local raw_loot
    # 5. VULNERABILITY RESULTS
    echo -e "\n[!] VULNERABILITY REPORT (NUCLEI)" >> "$final_report"
    if [[ -s "$OUTPUT_DIR/vulns_${target}.txt" ]]; then
        cat "$OUTPUT_DIR/vulns_${target}.txt" >> "$final_report"
    else
        echo "No significant vulnerabilities found." >> "$final_report"
    fi

    
    # We expanded the search terms to be more "useful"
    raw_loot=$(grep -rEi "password|token|api_key|admin|root|secret|key|set-cookie|db_|mysql|aws|disallow" "$OUTPUT_DIR" \
        --exclude="LOOT_*" --exclude="SUMMARY_*" 2>/dev/null)

    if [[ -n "$raw_loot" ]]; then
        echo "$raw_loot" | sed -E "
            s|${OUTPUT_DIR}/||g;
            s/\\\\x20/ /g; 
            s/\\\\r\\\\n/ /g; 
            s/\\\\n/ /g; 
            s/[[:space:]]+/ /g;
            s/SF:[^ ]* //g; 
            s/SF://g;
            s/\r//g" >> "$loot_file"
        
        log_info "Looting complete for $target."
        echo -e "\n[!] Check $(basename "$loot_file") for cleaned findings." >> "$final_report"
    else
        echo "No high-entropy secrets or sensitive keywords found." >> "$loot_file"
    fi
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    execute "$1"
fi
