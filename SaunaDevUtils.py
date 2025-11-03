from pymodbus.client import ModbusSerialClient


class SaunaDevUtils:

    _fanModuleSlaveIdAddress = 2
    _defaultFanModuleSlaveId = 1
    _sensorSlaveIdAddress = 0x07D0
    _sensorBaudRateAddress = 0x07D1
    _sensorBaudRate2400 = 0
    _sensorBaudRate4800 = 1
    _sensorBaudRate9600 = 2
    _sensorDefaultBaudRate = _sensorBaudRate4800
    _sensorDefaultSlaveId = 1

    # Instantiates Modbus Serial Port client
    def getModbusSerialClient(self, baudrate):
        return ModbusSerialClient(port='/dev/ttyAMA0', baudrate=baudrate, timeout=3, retries=3)

    # ------------------------------- Modbus Device Configuration Functions ---------------------------------

    def setJpf4816SlaveId(self, baudrate, currentId, newId) -> str:
        client = self.getModbusSerialClient(baudrate)
        response = client.write_register(address=self._fanModuleSlaveIdAddress, value=newId, slave=currentId)
        if response.isError():
            return "Error Setting up New Slave ID for JPF4816 Fn Control Module."
        else:
            response = client.read_holding_registers(address=self._fanModuleSlaveIdAddress, slave=newId)
            if response.isError():
                return "Error Setting up New Slave ID for JPF4816 Fn Control Module. Cannot read device after configuring new SlaveId."
        client.close()
        return f"Success. Response: {response.registers}"


    def setSensorSlaveId(self, baudrate, currentId, newId) -> str:
        client = self.getModbusSerialClient(baudrate)
        response = client.write_register(address=self._sensorSlaveIdAddress, value=newId, slave=currentId)
        if response.isError():
            return "Error Setting up New Slave ID for Temp/Humidity Sensor."
        else:
            response = client.read_holding_registers(address=self._sensorSlaveIdAddress, slave=newId)
            if response.isError():
                return "Error Setting up New Slave ID for Temp/Humidity Sensor. Cannot read device after configuring new SlaveId."
        client.close()
        return f"Success. Response: {response.registers}"


    # This function is not going to work with the current modbus functions as the baudrate is set up during client
    # initialization.
    def setSensorBaudRate(self, currentBaudRate, newBaudrate, slaveId) -> str:
        client = self.getModbusSerialClient(currentBaudRate)
        br = self._sensorDefaultBaudRate
        if newBaudrate == 2400:
            br = self._sensorBaudRate2400
        elif newBaudrate == 4800:
            br = self._sensorBaudRate4800
        elif newBaudrate == 9600:
            br = self._sensorBaudRate9600
        else:
            return f"Baud Rate {newBaudrate} is not supported."
        response = client.write_register(address=self._sensorBaudRateAddress, value=br, slave=slaveId)
        if response.isError():
            return "Error Setting up New Baud Rate for Temp/Humidity Sensor."
        else:
            client.close()
            client = self.getModbusSerialClient(newBaudrate)
            response = client.read_holding_registers(address=self._sensorBaudRateAddress, slave=slaveId)
            if response.isError():
                return "Error Setting up New Baud Rate for Temp/Humidity Sensor. Cannot read device after configuring new SlaveId."
        client.close()
        return f"Success. Response: {response.registers}"
