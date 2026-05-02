import sys
import time
import logging
import re
from pymodbus.client import ModbusTcpClient

# --- SILENCE INTERNAL NOISE ---
logging.basicConfig()
modbus_log = logging.getLogger('pymodbus')
modbus_log.setLevel(logging.CRITICAL)

def parse_args():
    # Default values if arguments are missing
    args = {
        "ip": None, 
        "port": 502, 
        "mode": "read", 
        "address": 0, 
        "count": 1, 
        "slave": 1,
        "timeout": 2.0
    }
    
    for arg in sys.argv[1:]:
        if arg.startswith("-ip="): args["ip"] = arg.split("=", 1)[1]
        elif arg.startswith("-port="): args["port"] = int(arg.split("=", 1)[1])
        elif arg.startswith("-mode="): args["mode"] = arg.split("=", 1)[1].lower()
        elif arg.startswith("-address="): args["address"] = int(arg.split("=", 1)[1])
        elif arg.startswith("-count="): args["count"] = int(arg.split("=", 1)[1])
        elif arg.startswith("-slave="): args["slave"] = int(arg.split("=", 1)[1])
        elif arg.startswith("-timeout="): args["timeout"] = float(arg.split("=", 1)[1])
    return args

def run_tool():
    args = parse_args()
    
    if not args["ip"]:
        print("Snowcrash 1.0 - Modbus Diagnostic Tool")
        print("Usage: python script.py -ip=<IP> [options]")
        print("\nOptions:")
        print("  -port=502          Target port")
        print("  -mode=scan         Modes: read, read_input, scan, slave_scan")
        print("  -address=0         Starting register address")
        print("  -count=100         Number of registers to scan")
        print("  -slave=1           Unit/Slave ID")
        print("  -timeout=2.0       Network timeout in seconds")
        return

    client = ModbusTcpClient(args["ip"], port=args["port"], timeout=args["timeout"])
    
    try:
        if not client.connect():
            print(f"[!] Connection failed to {args['ip']}:{args['port']}")
            return

        print(f"[+] Connected to {args['ip']}:{args['port']}")

        # --- MODE: SLAVE SCAN (Checks IDs 1-255) ---
        if args["mode"] == "slave_scan":
            print(f"[*] Hunting active Slave IDs on {args['ip']}...")
            for sid in range(1, 256):
                # Try reading a single register to see if the ID responds
                res = client.read_holding_registers(args["address"], count=1, slave=sid)
                if res and not hasattr(res, 'isError'):
                    print(f"\n[!!!] HIT -> Slave ID {sid} is RESPONDING at address {args['address']}")
                elif hasattr(res, 'exception_code') and res.exception_code < 4:
                    # Codes 1-3 mean the Slave exists but the address/function is rejected
                    print(f"\n[+] ACTIVE -> Slave ID {sid} present (Exception {res.exception_code})")
                
                if sid % 10 == 0:
                    sys.stdout.write(f"{sid}.")
                    sys.stdout.flush()
            print("\n[*] Slave scan complete.")

        # --- MODE: REGISTER SCAN (Deep scan on one Slave) ---
        elif args["mode"] == "scan":
            print(f"[*] Scanning {args['count']} registers on Slave {args['slave']}...")
            for addr in range(args["address"], args["address"] + args["count"]):
                # Try Holding
                h_res = client.read_holding_registers(addr, count=1, slave=args["slave"])
                if h_res and not hasattr(h_res, 'isError'):
                    print(f"\n[!!!] HIT HOLDING | Addr {addr}: {h_res.registers[0]}")
                
                # Try Input
                i_res = client.read_input_registers(addr, count=1, slave=args["slave"])
                if i_res and not hasattr(i_res, 'isError'):
                    print(f"\n[!!!] HIT INPUT   | Addr {addr}: {i_res.registers[0]}")
                
                if addr % 10 == 0:
                    sys.stdout.write(".")
                    sys.stdout.flush()
                time.sleep(0.01) # High-speed scan

        # --- MODE: SINGLE READ ---
        elif args["mode"] == "read":
            res = client.read_holding_registers(args["address"], count=args["count"], slave=args["slave"])
            if res and not hasattr(res, 'isError'):
                print(f"[+] Read Success (Slave {args['slave']}): {res.registers}")
            else:
                print(f"[-] Read Failed: {res}")

    except KeyboardInterrupt:
        print("\n[!] User aborted.")
    finally:
        client.close()
        print("[*] Disconnected.")

if __name__ == "__main__":
    run_tool()
