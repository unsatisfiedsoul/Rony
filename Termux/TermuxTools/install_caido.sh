#!/data/data/com.termux/files/usr/bin/bash

# Define Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}[*] Cleaning up old attempts...${NC}"
rm -f caido-cli* # 1. Detect Architecture
ARCH=$(uname -m)
if [ "$ARCH" = "aarch64" ]; then
    CAIDO_ARCH="linux-aarch64"
elif [ "$ARCH" = "x86_64" ]; then
    CAIDO_ARCH="linux-x86_64"
else
    echo -e "${RED}[!] Unsupported architecture: $ARCH${NC}"
    exit 1
fi

# 2. Updated Version Link (v0.44.0)
VERSION="0.44.0"
URL="https://downloads.caido.io/releases/v${VERSION}/caido-cli-v${VERSION}-${CAIDO_ARCH}.tar.gz"
FILENAME="caido.tar.gz"

echo -e "${GREEN}[*] Downloading Caido v${VERSION} for ${ARCH}...${NC}"

# Using -c to resume and --tries for stability
wget --tries=3 "$URL" -O "$FILENAME"

# 3. Verify Download and Extract
if [ -f "$FILENAME" ] && [ s $(stat -c%s "$FILENAME") -gt 1000 ]; then
    echo -e "${GREEN}[*] Extraction in progress...${NC}"
    tar -xvzf "$FILENAME"
    
    # Caido extracts as 'caido-cli' - we rename it to 'caido' for ease
    chmod +x caido-cli
    mv caido-cli "$PREFIX/bin/caido"
    rm "$FILENAME"
    
    echo -e "${GREEN}[+] Success! Run it with: caido --listen 127.0.0.1:8080${NC}"
else
    echo -e "${RED}[!] Download failed or file is empty. Check your internet connection.${NC}"
    exit 1
fi
