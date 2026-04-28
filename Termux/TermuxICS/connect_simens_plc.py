import snap7

# The IP of the S7-1500
plc_ip = input('PLC IP: ' )

plc = snap7.client.Client()
try:
    # Connect to Port 102
    plc.connect(plc_ip, 0, 1) # Rack 0, Slot 1 for S7-1500
    if plc.get_connected():
        print(f"Successfully connected to {plc_ip}")
        # Example: Read the CPU state
        print(f"CPU State: {plc.get_cpu_state()}")
    plc.disconnect()
except Exception as e:
    print(f"Connection failed: {e}")
