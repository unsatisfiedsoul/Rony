#!/bin/bash

# 1. Update system and install dependencies
pkg update && pkg upgrade -y
pkg install wget tar curl termux-elf-cleaner patchelf glibc-repo -y
pkg install glibc glibc-runner -y

# 2. Fetch the latest download URL for Linux Aarch64 CLI
echo "Fetching latest Caido CLI download link..."
DOWNLOAD_URL=$(curl -s https://caido.download/releases/latest | grep -o 'https://[^"]*linux-aarch64.tar.gz' | head -n 1)

if [ -z "$DOWNLOAD_URL" ]; then
    DOWNLOAD_URL="https://caido.download/releases/latest/caido-cli-linux-aarch64.tar.gz"
fi

# 3. Download and Extract to Home directory
echo "Downloading to $HOME..."
wget -O "$HOME/caido.tar.gz" "$DOWNLOAD_URL"

echo "Extracting..."
tar -xvf "$HOME/caido.tar.gz" -C "$HOME"
chmod +x "$HOME/caido-cli"

# 4. Patch the binary for Termux compatibility
echo "Cleaning and patching binary..."
termux-elf-cleaner "$HOME/caido-cli"

# 5. Setup Persistence (Alias and Temp Directory)
echo "Setting up alias and temporary directories..."
mkdir -p "$HOME/tmp"

# Add alias to .zshrc (using \ to escape the $ so it writes literally to the file)
echo "alias caido='TMPDIR=\$HOME/tmp grun \$HOME/caido-cli'" >> ~/.zshrc

# 6. Final Execution
echo "---------------------------------------"
echo "Installation complete!"
echo "The alias 'caido' has been added to your .zshrc."
echo "Please run 'source ~/.zshrc' or restart Termux."
echo "---------------------------------------"

# Use the environment variable inline for the first run
TMPDIR=$HOME/tmp grun $HOME/caido-cli
