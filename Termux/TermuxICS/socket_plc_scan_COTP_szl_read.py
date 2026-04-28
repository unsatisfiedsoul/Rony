import socket
import time

# Target Configuration
TARGET_IP = input("IP: ")
PORT = 102

# 1. COTP Connection Request (Handshake)
# Targets Rack 0, Slot 2 (Common for S7-300/400)
COTP_CR = bytes.fromhex("0300001611e00000000100c1020100c2020102c0010a")

# 2. S7 Setup Communication
# Initialized the protocol parameters (PDU length, etc.)
S7_SETUP = bytes.fromhex("0300001902f08032010000000000080000f0000001000101e0")

# 3. S7 Read SZL (System Status List)
# Specifically requesting Module Identification (ID 0x0011, Index 0x0001)
S7_READ_ID = bytes.fromhex("0300002102f080320700000001000800080001120411440100ff09000400110001")

def scan_plc():
    try:
        # Create Socket
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(5)
        
        print(f"[*] Connecting to {TARGET_IP}...")
        client.connect((TARGET_IP, PORT))
        print("[+] TCP Connection Established.")

        # Step 1: COTP Handshake
        client.send(COTP_CR)
        response = client.recv(1024)
        if response and response[5] == 0xd0: # 0xd0 = Connection Confirm
            print("[+] COTP Handshake Successful.")
        else:
            print("[-] COTP Handshake Failed.")
            return

        # Step 2: S7 Setup
        client.send(S7_SETUP)
        response = client.recv(1024)
        print("[+] S7 Communication Setup sent.")

        # Step 3: Request Module Info
        time.sleep(0.5) # Small delay for industrial processing
        client.send(S7_READ_ID)
        response = client.recv(1024)

        if response:
            print(f"[+] Raw Response: {response.hex()}")
            # Attempt to extract printable ASCII (Module name/Serial)
            printable = "".join([chr(b) if 32 <= b <= 126 else "." for b in response])
            print(f"[+] Extracted Data: {printable}")
        else:
            print("[-] No response to ID request.")

    except Exception as e:
        print(f"[!] Error: {e}")
    finally:
        client.close()
        print("[*] Connection Closed.")

if __name__ == "__main__":
    scan_plc()
