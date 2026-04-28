#!/bin/bash

# Path to the script in Termux
NSE_PATH="$PREFIX/share/nmap/scripts/s7-enumerate.nse"

if [ ! -f "$NSE_PATH" ]; then
    echo "[!] S7 script missing. Downloading now..."
    curl -s -o "$NSE_PATH" https://raw.githubusercontent.com/digitalbond/Redpoint/master/s7-enumerate.nse
    nmap --script-updatedb
fi

echo -n "Enter PLC IP: "
read ip

echo "[+] Starting S7 Scan on $ip..."
# Using -sT because we are non-rooted
nmap -sT --script s7-enumerate -p 102 "$ip"
