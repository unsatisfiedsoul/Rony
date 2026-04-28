#!/data/data/com.termux/files/usr/bin/bash

# Colors for better visibility
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}[*] Starting updated Caido installation...${NC}"

# 1. Architecture Check
ARCH=$(uname -m)
if [ "$ARCH" = "aarch64" ]; then
    CAIDO_ARCH="linux-aarch64"
elif [ "$ARCH" = "x86_64" ]; then
    CAIDO_ARCH="linux-x86_64"
else
    echo -e "${RED}[!] Unsupported architecture: $ARCH${NC}"
    exit 1
fi

# 2. Latest Version (As of April 2026)
VERSION="0.56.0"
URL="https://caido.download/releases/v${VERSION}/caido-cli-v${VERSION}-${CAIDO_ARCH}.tar.gz"
FILENAME="caido_latest.tar.gz"

echo -e "${BLUE}[*] Downloading Caido v${VERSION} for ${ARCH}...${NC}"

# 3. Clean and Download
rm -f caido_latest.tar.gz caido-cli
pkg install wget tar openssl -y

# Using -c to resume and a proper User-Agent to avoid blocks
wget --user-agent="Mozilla/5.0" "$URL" -O "$FILENAME"

# 4. Verify and Extract
if [ -f "$FILENAME" ] && [ $(stat -c%s "$FILENAME") -gt 1000000 ]; then
    echo -e "${GREEN}[*] File downloaded successfully. Extracting...${NC}"
    tar -xvzf "$FILENAME"
    
    # Finalizing installation
    chmod +x caido-cli
    mv caido-cli "$PREFIX/bin/caido"
    rm "$FILENAME"
    
    echo -e "${GREEN}[+] Installation Finished!${NC}"
    echo -e "${BLUE}[*] Run: ${NC}caido --listen 127.0.0.1:8080"
else
    echo -e "${RED}[!] Error: Downloaded file is invalid or too small.${NC}"
    echo -e "${RED}[!] Try switching to a different DNS or check your network.${NC}"
    exit 1
fi
