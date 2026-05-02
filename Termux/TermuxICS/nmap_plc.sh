#!/bin/bash

# Use 'read' to get input into a variable
echo -n "Enter IP or Subnet (e.g., 192.168.0.1): "
read target_ip

echo "--- Starting Scan on $target_ip/24 ---"
# Scans the subnet to find active Siemens devices
nmap -sT -p 102,443,80,502 "$target_ip/24"

echo "--- Running S7 Enumeration on $target_ip ---"
# Specifically probes the target for PLC model and firmware
nmap -sT --script s7-enumerate -p 102 "$target_ip"

# For modbus operation info
nmap -p 502 --script modbus-discover "$target_ip"

# For broad industrial scan
nmap -Pn -sT -p 102,502,1911,9600,44818,47808 --script "modbus-discover or s7-info or enip-info or omron-info or fox-info or bracnet-info" "$target_ip"

# For aggressive modbus-info
nmap -p 502 --script modbus-discover --script-args modbus-discover.aggressive=true "$target_ip"
