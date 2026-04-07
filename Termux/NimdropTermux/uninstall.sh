#!/data/data/com.termux/files/usr/bin/bash

BLUE="\\033[94m"
GREEN="\\033[92m"
RED="\\033[91m"
RESET="\\033[0m"

echo -e "${BLUE}[*] Uninstalling NimDrop...${RESET}"

# Remove main script
rm -f $PREFIX/bin/nimdrop

# Remove tool directory
rm -rf $PREFIX/share/nimdrop

echo -e "${GREEN}[+] NimDrop uninstalled successfully${RESET}"
