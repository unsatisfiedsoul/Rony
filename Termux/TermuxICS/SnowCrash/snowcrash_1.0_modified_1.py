import sys
import json
import datetime
import os
import re
import time
import logging

# --- SILENCE INTERNAL LIBRARY LOGGING ---
logging.basicConfig()
log = logging.getLogger('pymodbus')
log.setLevel(logging.CRITICAL) # Only show critical errors, hide exceptions

# --- UNIVERSAL IMPORT BLOCK ---
try:
    from pymodbus.client import ModbusTcpClient
except ImportError:
    try:
        from pymodbus.client.sync import ModbusTcpClient
    except ImportError:
        print("[!] Pymodbus not found. Run: pip install pymodbus")
        sys.exit(1)

def parse_args():
    args = {
        "ip": None, "mode": None, "write_count": 1, 
        "address": 0, "count": 1, "value": None, "output": None
    }
    for arg in sys.argv[1:]:
        if arg.startswith("-ip="):
            args["ip"] = arg.split("=", 1)[1]
        elif arg.startswith("-mode="):
            mode_val = arg.split("=", 1)[1].lower()
            match = re.match(r"write-(\d+)", mode_val)
            if match:
                args["mode"] = "write-multi"; args["write_count"] = int(match.group(1))
            else:
                args["mode"] = mode_val
        elif arg.startswith("-address="):
            args["address"] = int(arg.split("=", 1)[1])
        elif arg.startswith("-count="):
            args["count"] = int(arg.split("=", 1)[1])
        elif arg.startswith("-value="):
            args["value"] = int(arg.split("=", 1)[1])
        elif arg.startswith("-output="):
            args["output"] = arg.split("=", 1)[1]
    return args

def write_log(entry, filename):
    if not filename: return
    entry["timestamp"] = datetime.datetime.now().isoformat()
    try:
        data = []
        if os.path.exists(filename):
            with open(filename, "r") as f:
                try:
                    data = json.load(f)
                    if not isinstance(data, list): data = [data]
                except: data = []
        data.append(entry)
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[!] Log Error: {e}")

def scan_registers(client, start, length, log_entry, output):
    """Deep scan: Tries both Holding and Input registers one-by-one."""
    print(f"[*] Deep Scanning {length} addresses starting at {start}...")
    print("[*] (Filtering out noise. Only successful hits will be shown.)")
    found_data = {"holding": {}, "input": {}}
    
    for addr in range(start, start + length):
        # 1. Try Holding Registers (Function 3)
        try:
            res = client.read_holding_registers(addr, count=1, slave=1)
            if res is not None and not hasattr(res, 'isError'):
                val = res.registers[0]
                print(f"[+] FOUND HOLDING -> Address {addr}: {val}")
                found_data["holding"][str(addr)] = val
        except:
            pass

        # 2. Try Input Registers (Function 4)
        try:
            res = client.read_input_registers(addr, count=1, slave=1)
            if res is not None and not hasattr(res, 'isError'):
                val = res.registers[0]
                print(f"[+] FOUND INPUT   -> Address {addr}: {val}")
                found_data["input"][str(addr)] = val
        except:
            pass

        time.sleep(0.1) # Added more delay to respect the server's CPU
            
    log_entry["scan_results"] = found_data
    print(f"[*] Scan complete. Found {len(found_data['holding'])} Holding and {len(found_data['input'])} Input registers.")
    write_log(log_entry, output)

if __name__ == "__main__":
    args = parse_args()
    
    if not args["ip"]:
        print("Usage: python script.py -ip=<IP> -mode=scan -address=0 -count=100")
        sys.exit(1)

    client = ModbusTcpClient(args["ip"])
    log_entry = {"ip": args["ip"], "mode": args["mode"], "address": args["address"]}

    try:
        if client.connect():
            print(f"[+] Connected to {args['ip']}")
            if args["mode"] == "scan":
                scan_registers(client, args["address"], args["count"], log_entry, args["output"])
            elif args["mode"] == "read":
                # Fallback to single read if requested
                res = client.read_holding_registers(args["address"], count=1, slave=1)
                if res and not hasattr(res, 'isError'):
                    print(f"[+] Register {args['address']}: {res.registers[0]}")
                else:
                    print(f"[!] Read failed at {args['address']}")
        else:
            print(f"[!] Failed to connect to {args['ip']}")
    finally:
        client.close()
        print("[*] Connection closed.")
