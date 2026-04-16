#!/data/data/com.termux/files/usr/bin/bash

# Define Colors for Output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}[*] Starting Caido CLI Installation for Termux...${NC}"

# 1. Update and Install Dependencies
echo -e "${BLUE}[*] Updating packages and installing dependencies...${NC}"
pkg update -y && pkg upgrade -y
pkg install wget tar openssl -y

# 2. Detect Architecture
ARCH=$(uname -m)
case "$ARCH" in
    aarch64) CAIDO_ARCH="linux-aarch64" ;;
    x86_64)  CAIDO_ARCH="linux-x86_64" ;;
    *) echo "Unsupported architecture: $ARCH"; exit 1 ;;
esac

echo -e "${GREEN}[+] Architecture detected: $ARCH${NC}"

# 3. Set Version and Download
# Note: Check caido.io for the latest version string if this becomes outdated.
VERSION="0.44.0" 
FILENAME="caido-cli-v${VERSION}-${CAIDO_ARCH}.tar.gz"
URL="https://downloads.caido.io/releases/v${VERSION}/${FILENAME}"

echo -e "${BLUE}[*] Downloading Caido v${VERSION}...${NC}"
wget -q --show-progress "$URL" -O "$FILENAME"

# 4. Extract and Install
echo -e "${BLUE}[*] Extracting and moving to /usr/bin...${NC}"
tar -xvzf "$FILENAME"
chmod +x caido-cli
mv caido-cli "$PREFIX/bin/caido"

# 5. Cleanup
rm "$FILENAME"

echo -e "${GREEN}[+] Installation Complete!${NC}"
echo -e "${BLUE}[*] Usage: Type 'caido --listen 127.0.0.1:8080' to start.${NC}"
echo -e "${BLUE}[*] Then open http://127.0.0.1:8080 in your browser.${NC}"
