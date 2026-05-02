import sys
import json
import datetime
import os
import re

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
        "address": None, "count": 1, "value": None, "output": None
    }
    for arg in sys.argv[1:]:
        if arg.startswith("-ip="):
            args["ip"] = arg.split("=", 1)[1]
        elif arg.startswith("-mode="):
            mode_val = arg.split("=", 1)[1].lower()
            match = re.match(r"write-(\d+)", mode_val)
            if match:
                args["mode"] = "write-multi"
                args["write_count"] = int(match.group(1))
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
        print(f"[!] Log writing failed: {e}")

def read_registers(client, address, count, log, output):
    print(f"[*] Reading {count} registers starting at address {address}...")
    try:
        # We use explicit keywords for everything except address. 
        # This bypasses the 'takes 2 positional arguments' error.
        result = client.read_holding_registers(address, count=count, slave=1)
        
        # Fallback for older versions if 'slave' keyword fails
        if isinstance(result, Exception): raise result

        if result is None:
            print("[!] Error: No response from server.")
        elif hasattr(result, 'isError') and result.isError():
            print(f"[!] Modbus Error: {result}")
        else:
            print("[+] Register values:")
            regs = getattr(result, 'registers', [])
            log["registers"] = {}
            for i, val in enumerate(regs):
                reg_addr = address + i
                log["registers"][str(reg_addr)] = val
                print(f"  Register {reg_addr}: {val}")
            log["result"] = "success"
    except TypeError:
        # Final fallback: If 'slave' fails, try 'unit' (for v1.5.2/2.x)
        try:
            result = client.read_holding_registers(address, count=count, unit=1)
            # ... process result same as above ...
            regs = getattr(result, 'registers', [])
            for i, val in enumerate(regs):
                print(f"  Register {address + i}: {val}")
        except Exception as e:
            print(f"[!] Argument error: {e}")
    except Exception as e:
        print(f"[!] General error: {e}")
    write_log(log, output)

def write_single_register(client, address, value, log, output):
    print(f"[*] Writing {value} to register {address}...")
    try:
        # Using keywords to ensure compatibility
        result = client.write_register(address, value=value, slave=1)
        if result is None or (hasattr(result, 'isError') and result.isError()):
            print(f"[!] Write failed: {result}")
        else:
            print("[+] Write successful.")
    except Exception as e:
        print(f"[!] Write error: {e}")
    write_log(log, output)

if __name__ == "__main__":
    args = parse_args()
    
    if not args["ip"] or args["address"] is None:
        print("Usage: python snowcrash.py -ip=<IP> -mode=read -address=<addr> -count=<n>")
        sys.exit(1)

    # Initialize Client
    client = ModbusTcpClient(args["ip"])
    log_entry = {"ip": args["ip"], "mode": args["mode"], "address": args["address"]}

    try:
        if client.connect():
            print(f"[+] Connected to {args['ip']}")
            if args["mode"] == "read":
                read_registers(client, args["address"], args["count"], log_entry, args["output"])
            elif args["mode"] == "write":
                write_single_register(client, args["address"], args["value"], log_entry, args["output"])
        else:
            print(f"[!] Failed to connect to {args['ip']}")
    finally:
        client.close()
        print("[*] Connection closed.")
