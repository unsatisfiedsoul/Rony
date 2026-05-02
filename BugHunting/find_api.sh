#!/bin/bash
DOMAIN="https://clickup.com"
# Extract JS paths, remove leading slashes, and ensure full URL
JS_FILES=$(curl -s "$DOMAIN" | grep -oP 'src="\K[^"]+\.js' | sed "s|^/||")

for file in $JS_FILES; do
    FULL_URL="${DOMAIN}/${file}"
    echo "--- Scanning: $FULL_URL ---"
    
    # Download once, search multiple patterns
    CONTENT=$(curl -s "$FULL_URL")
    
    # 1. Look for API Keys/Tokens
    echo "$CONTENT" | grep -Eoi "(key|token|secret|auth|authorization|api-key)[\"']?\s*[:=]\s*[\"'][a-zA-Z0-9_\-]{16,}" 
    
    # 2. Look for API Endpoints (URLs)
    echo "$CONTENT" | grep -Eo "https?://api\.[a-zA-Z0-9./_-]+"
done
