#!/bin/bash

# Automated recon pipeline
target=$1

if [ -z "$target" ]; then
    echo "Usage: ./recon.sh <domain>"
    exit 1
fi

# Locate the correct httpx binary
if [ -f "$HOME/go/bin/httpx" ]; then
    HTTPX_BIN="$HOME/go/bin/httpx"
elif command -v httpx &>/dev/null && httpx -version &>/dev/null; then
    HTTPX_BIN="httpx"
else
    echo "[!] ProjectDiscovery httpx not found."
    exit 1
fi

# Create a workspace
mkdir -p "$target"
cd "$target" || exit

echo "[*] 1. Subdomain enumeration: subfinder"
subfinder -d "$target" -silent | sort -u > subs.txt

# FALLBACK LOGIC: If subs.txt is empty, add the main target to it
if [ ! -s subs.txt ]; then
    echo "[!] No subdomains found. Adding main domain $target to list."
    echo "$target" > subs.txt
else
    # Also ensure the root domain is included if subdomains WERE found
    echo "$target" >> subs.txt
    sort -u subs.txt -o subs.txt
fi

echo "[*] 2. Checking live hosts: httpx"
$HTTPX_BIN -l subs.txt -silent -o live.txt

if [ ! -s live.txt ]; then
    echo "[!] No live hosts detected. Check your connection or the target."
    exit 1
fi

echo "[*] 3. Crawling live hosts: katana"
# Using -list for file input
katana -list live.txt -silent -d 2 > urls.txt

echo "[*] 4. Running vulnerability scan: nuclei"
nuclei -l live.txt -severity medium,high,critical -silent -o vulns.txt

echo "[*] 5. Discovering hidden content: ffuf"
# Update this path to your actual wordlist location
WORDLIST="/usr/share/wordlists/dirb/common.txt"
if [ ! -f "$WORDLIST" ]; then
    WORDLIST="$HOME/wordlists/common.txt"
fi

if [ -f "$WORDLIST" ]; then
    mkdir -p fuzzing
    while IFS= read -r url; do
        # Clean URL for filename
        safe_name=$(echo "$url" | sed 's/[^a-zA-Z0-9]/_/g')
        echo "    > Fuzzing: $url"
        ffuf -u "$url/FUZZ" -w "$WORDLIST" -mc 200,301,302 -o "fuzzing/${safe_name}.json"
    done < live.txt
else
    echo "[!] Skipping ffuf: Wordlist not found at $WORDLIST"
fi

echo "--------------------------------------------------"
echo "[+] Pipeline Complete! Results in '$target/'"
echo "[+] Final Step: 6. Manual Testing"
echo "--------------------------------------------------"
