#!/data/data/com.termux/files/usr/bin/bash
execute() {
    target=$1
    log INFO "Recon"
    nmap -sn -T4 "$target" > /dev/null
}
