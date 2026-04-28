#!/bin/python

from pymodbus.client import ModbusTcpClient
ip = input("Ip: ")
port=502
client = ModbusTcpClient(ip,port)

if client.connect():
	print('PLC is connected through modbus')
else:
	print('PLC not connected')

result0 = client.read_holding_registers(address=0, count=1, slave=1)
if not result0.isError():
	package_type = result0.registers[0]
	print(f"HR0 (Package type): {package_type}")
	if package_type ==0:
		print(" Happy Cristmas Present")
	elif package_type==1:
		print(" Chocolate Eggs")
	elif package_type==2:
		print(" Ester Baskets")

result1 = client.read_holding_registers(address=1, count=1, slave=1)

if not result1.isError():
	zone = result1.registers[0]
	print(f"HR1 (Delivey Zone): {zone}")
	if zone==10:
		print(" Warning: Ocean dump zone")
	else:
		print(f" Normal Delivery Zone")


result2 = client.read_holding_registers(address=4, count=1, slave=1)
if not result2.isError():
	signature = result2.registers[0]
	print(f"HR4 (System Signature): {signature}")
	if signature==666:
		print(f" Eggsploit Detected, King Malhare signature.")


result3 = client.read_coils(address=10, count=1, slave=1)
if not result3.isError():
	varification = result3.bits[0]
	print(f"C10 (Inventory Varification): {varification}")
	if not varification:
		print(" DISABLED - System not checking stocks")


result4 = client.read_coils(address=11, count=1, slave=1)
if not result4.isError():
    protection = result4.bits[0]
    print(f"C11 (Protection/Override): {protection}")
    if protection:
        print(" Active - Changes are being monitored")

result5 = client.read_coils(address=15, count=1, slave=1)
if not result5.isError():
    armed = result5.bits[0]
    print(f"C15 (Self-destruct Armed): {armed}")
    if not armed:
        print(" Not armed yet -  Safe for now")

