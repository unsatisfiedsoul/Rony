# Example of what you could run in a Python script within Termux
from scapy.all import *
# PROFINET DCP Identify Request (EtherType 0x8892)
packet = Ether(dst="01:0e:cf:00:00:00")/Raw(load="\xfe\xfe\x05\x00\x04\x00\x00\x03\x00\x00")
sendp(packet, iface="wlan0") # Or your specific interface
