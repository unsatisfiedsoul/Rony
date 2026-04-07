#!/data/data/com.termux/files/usr/bin/bash

BLUE="\\033[94m"
GREEN="\\033[92m"
RED="\\033[91m"
RESET="\\033[0m"

echo -e "${BLUE}[*] Installing NimDrop for Termux...${RESET}"

# Check if running in Termux
if [[ ! -d /data/data/com.termux ]]; then
    echo -e "${RED}[!] This installer is for Termux only${RESET}"
    exit 1
fi

# Create bin directory if it doesn't exist
mkdir -p $PREFIX/bin

# Copy the main script
cp nimdrop $PREFIX/bin/
chmod +x $PREFIX/bin/nimdrop

# Create tool directory
mkdir -p $PREFIX/share/nimdrop

echo -e "${GREEN}[+] NimDrop installed successfully!${RESET}"
echo -e "${GREEN}[+] Run 'nimdrop -h' for help${RESET}"
