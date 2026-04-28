#!/data/data/com.termux/files/usr/bin/bash
detect_services() {
    scan_file=$1
    services=""
    grep -q "80/tcp open" "$scan_file" && services+="web "
    grep -q "445/tcp open" "$scan_file" && services+="smb "
    grep -q "22/tcp open" "$scan_file" && services+="ssh "
    echo "$services"
}
