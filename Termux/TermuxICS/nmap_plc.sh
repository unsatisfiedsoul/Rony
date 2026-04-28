#!/bin/bash

# Use 'read' to get input into a variable
echo -n "Enter IP or Subnet (e.g., 192.168.0.1): "
read target_ip

echo "--- Starting Scan on $target_ip/24 ---"
# Scans the subnet to find active Siemens devices
nmap -sT -p 102,443,80 "$target_ip/24"

echo "--- Running S7 Enumeration on $target_ip ---"
# Specifically probes the target for PLC model and firmware
nmap -sT --script s7-enumerate -p 102 "$target_ip"
