#!/bin/bash

# Automated recon pipeline
target=$1

if [ -z "$target" ]; then
    echo "Usage: ./recon.sh <domain>"
    exit 1
fi

# Locate the correct httpx binary (checking common Go paths)
if [ -f "$HOME/go/bin/httpx" ]; then
    HTTPX_BIN="$HOME/go/bin/httpx"
elif command -v httpx &>/dev/null && httpx -version &>/dev/null; then
    HTTPX_BIN="httpx"
else
    echo "[!] ProjectDiscovery httpx not found."
    echo "[!] Try: go install github.com/projectdiscovery/httpx/cmd/httpx@latest"
    exit 1
fi

# Create a workspace
mkdir -p "$target"
cd "$target" || exit

echo "[*] Subdomain enumeration for $target"
subfinder -d "$target" -silent | sort -u > subs.txt

if [ ! -s subs.txt ]; then
    echo "[!] No subdomains found for $target. Exiting."
    exit 1
fi

echo "[*] Checking live hosts"
# Use the identified binary path
$HTTPX_BIN -l subs.txt -silent -o live.txt

if [ ! -s live.txt ]; then
    echo "[!] No live hosts detected. Ensure $target is reachable."
    exit 1
fi

echo "[*] Crawling live hosts"
katana -list live.txt -silent -d 2 > urls.txt

echo "[*] Running vulnerability scan"
nuclei -l live.txt -severity medium,high,critical -silent -o vulns.txt

echo "--------------------------------------------------"
echo "[+] Done! Results in the '$target' directory."
echo "    - Subdomains: $(wc -l < subs.txt)"
echo "    - Live Hosts: $(wc -l < live.txt)"
echo "--------------------------------------------------"
