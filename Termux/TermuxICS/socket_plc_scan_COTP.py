import socket

# Target details
ip = input("IP: ")
port = 102

# This is a standard COTP Connection Request (CR) packet
# It's the "Hello" of the Siemens S7 protocol
handshake = bytes.fromhex("0300001611e00000000100c1020100c2020102c0010a")

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    s.connect((ip, port))
    print("[+] TCP Connection established.")
    
    s.send(handshake)
    response = s.recv(1024)
    
    if response:
        print(f"[+] PLC Responded: {response.hex()}")
    else:
        print("[-] Connection closed by PLC without data.")
except Exception as e:
    print(f"[-] Error: {e}")
finally:
    s.close()
