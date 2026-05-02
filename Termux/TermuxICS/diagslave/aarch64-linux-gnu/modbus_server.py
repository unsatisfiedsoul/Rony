from pymodbus.server import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext

def run_server(port):
    # Create a datastore with some dummy data
    # Registers 0-99 will be initialized with the value 42
    store = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, [1]*100),
        co=ModbusSequentialDataBlock(0, [1]*100),
        hr=ModbusSequentialDataBlock(0, [42]*100),
        ir=ModbusSequentialDataBlock(0, [42]*100)
    )
    context = ModbusServerContext(slaves=store, single=True)
    
    print(f"[*] Starting Local Modbus Server on port {port}...")
    print("[*] Values at Address 0-99 are set to: 42")
    StartTcpServer(context=context, address=("127.0.0.1", port))

if __name__ == "__main__":
    # We use 1502 because 502 requires root on Android/Termux
    run_server(1502)
