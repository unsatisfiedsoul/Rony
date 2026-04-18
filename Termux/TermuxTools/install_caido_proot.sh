#!/data/data/com.termux/files/usr/bin/bash

# 1. Ensure proot-distro is ready
pkg install proot-distro wget -y

# 2. Reinstall Debian to be safe
proot-distro remove debian
proot-distro install debian

# 3. Download and place the binary correctly inside Debian
echo "[*] Setting up Caido inside Debian..."
proot-distro login debian -- bash -c "
    apt update && apt install -y wget tar;
    cd /usr/local/bin;
    wget -O caido.tar.gz 'https://caido.download/releases/v0.56.0/caido-cli-v0.56.0-linux-aarch64.tar.gz';
    tar -xvf caido.tar.gz --strip-components=0;
    mv caido-cli caido; 
    chmod +x caido;
    rm caido.tar.gz;
"

# 4. Create a robust launch script
cat << 'EOF' > ~/start-caido.sh
#!/data/data/com.termux/files/usr/bin/bash
echo "[*] Launching Caido on http://127.0.0.1:8080"
proot-distro login debian -- /usr/local/bin/caido -l 0.0.0.0:8080
EOF

chmod +x ~/start-caido.sh
echo "[+] DONE! Run ./start-caido.sh to begin."
