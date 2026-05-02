import sys
import time
import logging
from pymodbus.client import ModbusTcpClient

# --- SILENCE ALL NOISE ---
logging.basicConfig()
modbus_log = logging.getLogger('pymodbus')
modbus_log.setLevel(logging.CRITICAL)

def parse_args():
    args = {
        "ip": None, "port": 502, "mode": "read", 
        "address": 0, "count": 1, "slave": 1, "timeout": 2.0
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
        print("Usage: python script.py -ip=<IP> [options]")
        return

    client = ModbusTcpClient(args["ip"], port=args["port"], timeout=args["timeout"])
    
    try:
        if not client.connect():
            print(f"[!] Connection failed to {args['ip']}:{args['port']}")
            return

        print(f"[+] Connected to {args['ip']}:{args['port']}")

        if args["mode"] == "slave_scan":
            print(f"[*] Hunting active Slave IDs (1-255)...")
            for sid in range(1, 256):
                res = client.read_holding_registers(args["address"], count=1, slave=sid)
                # Check for registers OR lack of error attribute
                if res and (hasattr(res, 'registers') or not hasattr(res, 'isError')):
                    print(f"\n[!!!] HIT -> Slave ID {sid} responded.")
                elif sid % 10 == 0:
                    sys.stdout.write(f"{sid}.")
                    sys.stdout.flush()

        elif args["mode"] == "scan":
            print(f"[*] Scanning {args['count']} registers on Slave {args['slave']}...")
            for addr in range(args["address"], args["address"] + args["count"]):
                h_res = client.read_holding_registers(addr, count=1, slave=args["slave"])
                if h_res and hasattr(h_res, 'registers'):
                    print(f"\n[!!!] HIT HOLDING | Addr {addr}: {h_res.registers[0]}")
                
                i_res = client.read_input_registers(addr, count=1, slave=args["slave"])
                if i_res and hasattr(i_res, 'registers'):
                    print(f"\n[!!!] HIT INPUT   | Addr {addr}: {i_res.registers[0]}")
                
                if addr % 10 == 0: sys.stdout.write("."); sys.stdout.flush()
                time.sleep(0.01)

        elif args["mode"] == "read":
            res = client.read_holding_registers(args["address"], count=args["count"], slave=args["slave"])
            # Success check: does it have registers?
            if res and hasattr(res, 'registers'):
                print(f"[!] Success (Slave {args['slave']}): {res.registers}")
            else:
                print(f"[-] Read Failed: {res}")

    except KeyboardInterrupt:
        print("\n[!] Aborted.")
    finally:
        client.close()
        print("[*] Disconnected.")

if __name__ == "__main__":
    run_tool()
