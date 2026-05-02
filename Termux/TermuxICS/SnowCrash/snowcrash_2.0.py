import sys
import time
import logging
from pymodbus.client import ModbusTcpClient

# --- SILENCE ALL NOISE ---
logging.basicConfig()
log = logging.getLogger('pymodbus')
log.setLevel(logging.CRITICAL)

def parse_args():
    # Defaults
    args = {
        "ip": None, 
        "port": 502, 
        "mode": "read", 
        "address": 0, 
        "count": 1, 
        "slave": 1, 
        "timeout": 2.5
    }
    for arg in sys.argv[1:]:
        if "=" in arg:
            k, v = arg.split("=", 1)
            k = k.lstrip("-")
            # Convert to int if numeric, else keep as string
            args[k] = int(v) if v.isdigit() else v
    return args

def run():
    a = parse_args()
    if not a["ip"]: 
        print("Usage: python script.py -ip=127.0.0.1 -port=1502 -mode=read -address=0 -slave=1")
        return
    
    # Initialize client
    c = ModbusTcpClient(a["ip"], port=int(a["port"]), timeout=float(a["timeout"]))
    
    if not c.connect(): 
        print(f"[!] Target {a['ip']}:{a['port']} - Connection Failed.")
        return
    
    print(f"[+] Targeting {a['ip']}:{a['port']}")

    try:
        if a["mode"] == "slave_scan":
            print("[*] Searching for any responsive Slave ID (1-255)...")
            for s in range(1, 256):
                # Explicit keywords to avoid TypeError
                r = c.read_holding_registers(address=int(a["address"]), count=1, slave=s)
                if r is not None:
                    # Check if response contains valid data or just a standard exception
                    status = "SUCCESS" if not hasattr(r, 'isError') or not r.isError() else f"ACTIVE (Exception {r.exception_code})"
                    if "ACTIVE" in status or "SUCCESS" in status:
                        print(f"\n[!!!] ID {s} is {status}")
                if s % 20 == 0: 
                    sys.stdout.write(f"{s}.")
                    sys.stdout.flush()
        
        elif a["mode"] == "read":
            # Explicit keywords used here to fix the TypeError
            r = c.read_holding_registers(address=int(a["address"]), count=int(a["count"]), slave=int(a["slave"]))
            
            if r is not None and hasattr(r, 'registers'):
                print(f"[!] Data Found: {r.registers}")
            else:
                # Handle error response objects
                err_msg = f"Exception {r.exception_code}" if hasattr(r, 'exception_code') else "No response"
                print(f"[-] Read Failed: {err_msg}")

    except Exception as e:
        print(f"[!] Runtime Error: {e}")
    finally:
        c.close()
        print("[*] Disconnected.")

if __name__ == "__main__":
    run()
