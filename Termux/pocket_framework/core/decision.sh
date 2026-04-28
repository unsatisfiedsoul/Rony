#!/data/data/com.termux/files/usr/bin/bash

# This script is sourced by the engine or modules to provide service detection.

detect_services() {
    local scan_file="$1"
    local found_services=""

    # 1. Validation: Ensure the scan file exists and is not empty
    if [[ ! -s "$scan_file" ]]; then
        log_warn "Scan file $scan_file is empty or missing. No services detected."
        echo ""
        return 1
    fi

    # 2. Define Service Mapping (Port/Protocol -> Keyword)
    # You can easily add more services to this list
    local -A service_map=(
        ["80/tcp open"]="web"
        ["443/tcp open"]="web"
        ["445/tcp open"]="smb"
        ["139/tcp open"]="smb"
        ["22/tcp open"]="ssh"
        ["21/tcp open"]="ftp"
    )

    # 3. Parse the file
    # We loop through our map and check if the pattern exists in the scan file
    for pattern in "${!service_map[@]}"; do
        if grep -q "$pattern" "$scan_file"; then
            local service_name="${service_map[$pattern]}"
            
            # Append service name if it's not already in the list
            if [[ ! "$found_services" =~ "$service_name" ]]; then
                found_services+="$service_name "
            fi
        fi
    done

    # 4. Return the result (trimmed)
    echo "${found_services% }"
}
