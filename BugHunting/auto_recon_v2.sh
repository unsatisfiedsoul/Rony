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
    echo "[!] ProjectDiscovery httpx not found. Please install it."
    exit 1
fi

# Check for dirb
if ! command -v dirb &>/dev/null; then
    echo "[!] dirb is not installed. Please install it (e.g., sudo apt install dirb)."
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
$HTTPX_BIN -l subs.txt -silent -o live.txt

if [ ! -s live.txt ]; then
    echo "[!] No live hosts detected."
    exit 1
fi

echo "[*] Crawling live hosts with Katana"
katana -list live.txt -silent -d 2 > urls.txt

echo "[*] Running directory brute-forcing with dirb"
# We loop through live hosts to run dirb on each
# -S (Silent mode), -o (Output file)
touch dirb_results.txt
while IFS= read -r url; do
    echo "    > Scanning: $url"
    dirb "$url" -S -o tmp_dirb.txt
    if [ -f tmp_dirb.txt ]; then
        cat tmp_dirb.txt >> dirb_results.txt
        rm tmp_dirb.txt
    fi
done < live.txt

echo "[*] Running vulnerability scan with Nuclei"
nuclei -l live.txt -severity medium,high,critical -silent -o vulns.txt

echo "--------------------------------------------------"
echo "[+] Done! Results in the '$target' directory."
echo "[+] Summary:"
echo "    - Subdomains:   $(wc -l < subs.txt)"
echo "    - Live Hosts:   $(wc -l < live.txt)"
echo "    - Dirb Finds:   $(grep -c "DIRECTORY" dirb_results.txt 2>/dev/null || echo 0) potential paths"
echo "    - Vulns Found:  $(wc -l < vulns.txt 2>/dev/null || echo 0)"
echo "--------------------------------------------------"
