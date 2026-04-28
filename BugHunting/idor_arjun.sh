#!/bin/bash

TARGET=$1

if [ -z "$TARGET" ]; then
    echo "Usage: ./scan_idor.sh <domain.com>"
    exit 1
fi

echo "[+] Starting recon for $TARGET..."

# 1. Enumerate subdomains
subfinder -d "$TARGET" -silent -o subdomains.txt

if [ ! -s subdomains.txt ]; then
    echo "[-] No subdomains found. Check subfinder installation."
    exit 1
fi

# 2. Probing for live endpoints using Python httpx
echo "[+] Probing for live endpoints..."
> endpoints.txt

while read -r domain; do
    # Since Python httpx needs a URL, we try https first
    # We use --follow-redirects to find the actual live location
    if httpx "https://$domain" --follow-redirects > /dev/null 2>&1; then
        echo "https://$domain" >> endpoints.txt
        echo "[FOUND] https://$domain"
    elif httpx "http://$domain" --follow-redirects > /dev/null 2>&1; then
        echo "http://$domain" >> endpoints.txt
        echo "[FOUND] http://$domain"
    fi
done < subdomains.txt

# 3. Final Check and Arjun Execution
if [ -s endpoints.txt ]; then
    echo "[+] Running Arjun on discovered URLs..."
    arjun -i endpoints.txt -t 5 -oT arjun_results.txt
    echo "[+] Done! Results saved in arjun_results.txt"
else
    echo "[-] No live endpoints discovered."
fi
