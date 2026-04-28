# S7 Request: Read SZL ID 0x0011 Index 0x0001 (Module Identification)
id_request = bytes.fromhex("0300002102f080320100000001000c00000401120a10020001000000010000")

s.send(id_request)
full_info = s.recv(1024)
print(f"[+] PLC Details: {full_info.hex()}")
