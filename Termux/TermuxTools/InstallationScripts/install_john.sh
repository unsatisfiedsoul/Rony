#!/bin/bash

# 1. Define Paths
TOOLS_DIR="$HOME/Tools"
JOHN_DIR="$TOOLS_DIR/john"
ZSHRC="$HOME/.zshrc"

echo "Checking dependencies..."
pkg update && pkg upgrade -y
pkg install git make clang binutils -y

# 2. Create Tools directory if it doesn't exist
mkdir -p "$TOOLS_DIR"

# 3. Clone John the Ripper (Bleeding-Jumbo version)
if [ -d "$JOHN_DIR" ]; then
    echo "John directory already exists. Skipping clone..."
else
    echo "Cloning John the Ripper from GitHub..."
    git clone https://github.com/openwall/john -b bleeding-jumbo "$JOHN_DIR"
fi

# 4. Build from source
echo "Compiling John... This may take a few minutes."
cd "$JOHN_DIR/src"
./configure
make -s clean && make -s

# 5. Setup Aliases in .zshrc
echo "Setting up aliases in $ZSHRC..."

# Create a backup of .zshrc just in case
cp "$ZSHRC" "${ZSHRC}.bak"

# Function to add alias if it doesn't exist
add_alias() {
    grep -q "alias $1=" "$ZSHRC" || echo "alias $1='$JOHN_DIR/run/$1'" >> "$ZSHRC"
}

add_alias "john"
add_alias "zip2john"
add_alias "rar2john"
add_alias "pdf2john"
add_alias "office2john"
add_alias "ssh2john"
add_alias "keepass2john"

echo "----------------------------------------"
echo "Installation Complete!"
echo "Please run: source ~/.zshrc"
echo "You can then use 'john' or 'zip2john' from anywhere."
echo "----------------------------------------"
