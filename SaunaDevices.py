import time
import atexit
from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusException
from ErrorManager import ErrorManager
from SaunaContext import SaunaContext


class SaunaDevices:

    # Sauna Context Manager
    _ctx = None

    # RS485 Client
    _rs485Client = None

    # Sensor Module Configuration
    _sensorModuleRs485SlaveId = 1
    _temperatureAddress = 1
    _humidityAddress = 0
    _lastHotRoomTemperatureC = 0
    _lastHotRoomHumidity = 0

    # Relay Module Configuration
    _relayModuleRs485SlaveId = 2
    _heaterCoilId = 0
    _notUsedCoilId = 1
    _rightFanCoilId = 2
    _leftFanCoilId = 3
    _lastFanRelayStatus = [False, False]

    # Fan Module Configuration
    _fanControlModuleRs485SlaveId = 3
    _roomTempretureAddress = 0
    _fanStatusAddress = 1
    _fanSpeedAddress = 3
    _numberOfFansAddress = 6
    _fanFaultStatusAddress = 14
    _resetFanModuleGovernorAddress = 32
    _resetFanModuleGovernorValue = 170
    _lastRestingRoomTemp = 0
    _rightFanId = 1
    _leftFanId = 2
    _lastFanSpeed = [0, 0]
    _lastFanStatus = [False, False]

    # Errors Manager
    _errorMgr = None

    # Heater Data
    _lastTimeHeaterOff = time.time()
    _lastTimeHeaterOn = time.time()
    _lastHeaterOnStatus = False

    def __init__(self, ctx: SaunaContext):
        self._ctx = ctx
        self._rs485Client = ModbusSerialClient(port=self._ctx.getRs485SerialPort(),
                                               baudrate=self._ctx.getRs485SerialBaudRate(),
                                               # Timeout is optimized for devices.
                                               timeout=self._ctx.getRs485SerialTimeout(),
                                               retries=self._ctx.getRs485SerialRetries())
        self._rs485Client.connect()
        self._errorMgr = ErrorManager()
        # Initialize Relay Module
        self._setRelayStatus(self._notUsedCoilId, False)
        # Initialize Fans
        if self.getNumberOfFans() != self._ctx.getNumberOfFans():
            self.setNumberOfFans(self._ctx.getNumberOfFans())
        self.setFanSpeed(self._ctx.getFanSpeedPct())
        self._setFanRelayStatus(self._rightFanCoilId, self._ctx.getRightFanOnStatus())
        self._setFanRelayStatus(self._leftFanCoilId, self._ctx.getLeftFanOnStatus())
        # These 2 functions will populate _lastFanRelayStatus[]
        self._getFanRelayStatus(self._rightFanCoilId)
        self._getFanRelayStatus(self._leftFanCoilId)
        # This function will populate _lastRestingRoomTemp
        self.getRestingRoomTemp()
        # This function will populate _lastFanSpeed[]
        self._getFanSpeedRpm(self._rightFanId)
        self._getFanSpeedRpm(self._leftFanId)
        # This function will populate _lastFanStatus[]
        self._getFanStatus(self._rightFanId)
        self._getFanStatus(self._leftFanId)
        # This function will populate _lastHotRoomTemperatureC
        self.getHotRoomTemperature()
        # This function will populate _lastHotRoomHumidity
        self.getHotRoomHumidity()
        # Initialize Heater
        self.turnHeaterOff()
        # Release resources on exit
        atexit.register(self._onExit)

    # Release resources on exit
    def _onExit(self):
        self._rs485Client.close()

    # ---------------------------------------- Sauna Sensors ---------------------------------------

    def getHotRoomTemperature(self, system='F') -> int:
        response=self._modbus_read_holding_registers(self._temperatureAddress, self._sensorModuleRs485SlaveId)
        if response.isError():
            self._errorMgr.raiseSensorModuleError('Cannot Read Temperature Sensor.')
        else:
            self._errorMgr.eraseSensorModuleError()
            self._lastHotRoomTemperatureC = response.registers[0] / 10
        if system == 'F':
            return round((self._lastHotRoomTemperatureC * 9 / 5) + 32)
        else:
            return round(self._lastHotRoomTemperatureC)

    def getHotRoomHumidity(self) -> int:
        response=self._modbus_read_holding_registers(self._humidityAddress, self._sensorModuleRs485SlaveId)
        if response.isError():
            self._errorMgr.raiseSensorModuleError('Cannot Read Humidity Sensor.')
        else:
            self._errorMgr.eraseSensorModuleError()
            self._lastHotRoomHumidity = response.registers[0] / 10
        return round(self._lastHotRoomHumidity)

    def getRestingRoomTemp(self, system='F') -> int:
        response=self._modbus_read_holding_registers(self._roomTempretureAddress, self._fanControlModuleRs485SlaveId)
        if response.isError():
            self._errorMgr.raiseFanModuleError('Cannot get Resting Room Temperature. E1')
        else:
            self._errorMgr.eraseFanModuleError()
            self._lastRestingRoomTemp = response.registers[0] - 40
        if system == 'F':
            return round((self._lastRestingRoomTemp * 9 / 5) + 32)
        return self._lastRestingRoomTemp


    # ---------------------------------- Sauna Heater Functions ----------------------------------

    def isHeaterOn(self) -> bool:
        response = self._modbus_read_coils(self._heaterCoilId, self._relayModuleRs485SlaveId)
        if response.isError():
            self._errorMgr.raiseRelayModuleError('Cannot get Heater Status.')
        else:
            self._errorMgr.eraseRelayModuleError()
            self._lastHeaterOnStatus = response.bits[self._heaterCoilId]
        return self._lastHeaterOnStatus

    def isHeaterOff(self) -> bool:
        return not self.isHeaterOn()

    def setHeaterRelay(self, status: bool) -> None:
        response = self._modbus_write_coil(self._heaterCoilId, status, self._relayModuleRs485SlaveId)
        if response.isError():
            self._errorMgr.raiseRelayModuleError('Cannot Turn the Heater On or Off.')
        else:
            self._errorMgr.eraseRelayModuleError()
            # If heater is actually getting turned on with this call
            if status and not self._lastHeaterOnStatus:
                self._lastTimeHeaterOff = time.time()
            # If heater is actually getting turned off with this call
            if not status and self._lastHeaterOnStatus:
                self._lastTimeHeaterOn = time.time()
            self._lastHeaterOnStatus = status

    def turnHeaterOn(self) -> None:
        self.setHeaterRelay(True)

    def turnHeaterOff(self) -> None:
        self.setHeaterRelay(False)

    # ------------------------------------- Vent Fans Functions -------------------------------------

    def _setRelayStatus(self, relayCoilId: int, state: bool) -> None:
        response = self._modbus_write_coil(relayCoilId, state, self._relayModuleRs485SlaveId)
        if response.isError():
            self._errorMgr.raiseRelayModuleError('Cannot Manipulate Relays.')
        else:
            self._errorMgr.eraseRelayModuleError()

    def _getFanRelayStatus(self, fanCoilId: int) -> bool:
        response = self._modbus_read_coils(fanCoilId, self._relayModuleRs485SlaveId)
        if response.isError():
            self._errorMgr.raiseRelayModuleError('Cannot Get Fan Status.')
        else:
            self._errorMgr.eraseRelayModuleError()
            self._lastFanRelayStatus[fanCoilId - 2] = response.bits[0]
        return self._lastFanRelayStatus[fanCoilId - 2]

    def _setFanRelayStatus(self, fanCoilId: int, state: bool) -> None:
        response = self._modbus_write_coil(fanCoilId, state, self._relayModuleRs485SlaveId)
        if response.isError():
            self._errorMgr.raiseRelayModuleError('Cannot Turn a Fan On or Off.')
        else:
            self._errorMgr.eraseRelayModuleError()
            self._lastFanRelayStatus[fanCoilId - 2] = state

    # fanId - either _rightFanId or _leftFanId
    def _getFanStatus(self, fanId) -> bool:
        # low 4 bits correspond to 4 fans, from right to left, the most right bit corresponds to fan 1,
        # 0 means the fan stops and 1 means the fan is running
        response = self._modbus_read_holding_registers(self._fanStatusAddress, self._fanControlModuleRs485SlaveId)
        if response.isError():
            self._errorMgr.raiseFanModuleError('Cannot Get Fan Status from Fan Module.RelayModule')
        else:
            self._errorMgr.eraseFanModuleError()
            self._lastFanStatus[fanId-1] = (response.registers[0] & fanId) > 0
        return self._lastFanStatus[fanId-1]

    def _getFanSpeedRpm(self, fanId: int) -> int:
        response = self._modbus_read_holding_registers(6 + fanId, self._fanControlModuleRs485SlaveId)
        if response.isError():
            self._errorMgr.raiseFanModuleError('Cannot Get Fan Speed.')
        else:
            self._errorMgr.eraseFanModuleError()
            self._lastFanSpeed[fanId - 1] = response.registers[0]
        return self._lastFanSpeed[fanId - 1]

    def getLeftFanSpeedRpm(self) -> int:
        return self._getFanSpeedRpm(self._leftFanId)

    def getRightFanSpeedRpm(self) -> int:
        return self._getFanSpeedRpm(self._rightFanId)

    # Sets speed for all fans. 0% ... 100%. Most fans will start running at 10% or more
    def setFanSpeed(self, speedPct: int) -> None:
        response = self._modbus_write_register(self._fanSpeedAddress, speedPct, self._fanControlModuleRs485SlaveId)
        if response.isError():
            self._errorMgr.raiseFanModuleError('Cannot Change Fan Speed.')
        else:
            self._errorMgr.eraseFanModuleError()
            self._ctx.setFanSpeedPct(speedPct)      # Save as default

    def isRightFanOn(self) -> bool: 
        return self._getFanRelayStatus(self._rightFanCoilId) and \
               self._getFanStatus(self._rightFanId) and \
               self._getFanSpeedRpm(self._rightFanId) > 0

    def isRightFanOff(self) -> bool:
        return not self.isRightFanOn()

    def isLeftFanOn(self) -> bool:
        return self._getFanRelayStatus(self._leftFanCoilId) and \
               self._getFanStatus(self._leftFanId) and \
               self._getFanSpeedRpm(self._leftFanId) > 0

    def isLeftFanOff(self) -> bool:
        return not self.isLeftFanOn()

    def turnLeftFanOn(self) -> None:
        self._setFanRelayStatus(self._leftFanCoilId, True)
        self._ctx.setLeftFanOnStatus(True)                  # Save as default

    def turnLeftFanOff(self) -> None:
        self._setFanRelayStatus(self._leftFanCoilId, False)
        self._ctx.setLeftFanOnStatus(False)                 # Save as default

    def turnRightFanOn(self) -> None:
        self._setFanRelayStatus(self._rightFanCoilId, True) 
        self._ctx.setRightFanOnStatus(True)                 # Save as default

    def turnRightFanOff(self) -> None:
        self._setFanRelayStatus(self._rightFanCoilId, False)
        self._ctx.setRightFanOnStatus(False)                # Save as default

    def getNumberOfFans(self) -> int:
        response = self._modbus_read_holding_registers(self._numberOfFansAddress, self._fanControlModuleRs485SlaveId)
        if response.isError():
            self._errorMgr.raiseFanModuleError('Cannot Get Number of Fans.')
            return self._ctx.getNumberOfFans()
        else:
            self._errorMgr.eraseFanModuleError()
            return response.registers[0]

    def setNumberOfFans(self, nFans: int) -> None:
        response = self._modbus_write_register(self._numberOfFansAddress, nFans, self._fanControlModuleRs485SlaveId)
        if response.isError():
            self._errorMgr.raiseFanModuleError('Cannot Set Number of Fans.')
        else:
            self._errorMgr.eraseFanModuleError()
            self._ctx.setNumberOfFans(nFans)        # Set as default

    def _checkFanFaultStatus(self, fanId: int) -> bool:
        response = self._modbus_read_holding_registers(self._fanFaultStatusAddress, self._fanControlModuleRs485SlaveId)
        if response.isError():
            self._errorMgr.raiseFanModuleError('Cannot Read Fan Status.')
            return True
        else:
            self._errorMgr.eraseFanModuleError()
            # Bit set to 0 corresponds to error
            return (response.registers[0] & fanId) == 0

    def isLeftFanOk(self) -> bool:
        return not self._checkFanFaultStatus(self._leftFanId)

    def isRightFanOk(self) -> bool:
        return not self._checkFanFaultStatus(self._rightFanId)

    def _resetFanModuleGovernor(self) -> None:
        response = self._modbus_write_register(self._resetFanModuleGovernorAddress, 
                                               self._resetFanModuleGovernorValue, 
                                               self._fanControlModuleRs485SlaveId)
        if response.isError():
            self._errorMgr.raiseFanModuleError('Cannot Reset Fan Module.')
        else:
            self._errorMgr.eraseFanModuleError()


# ----------------------------------- RS485 Modbus Helpers -------------------------------------

    def _modbus_read_holding_registers(self, address: int, slave: int, count: int=1) -> int:
        try:
            response = self._rs485Client.read_holding_registers(address, count=1, slave=slave)
            self._errorMgr.eraseModbusError()
        except ModbusException as e:
            self._errorMgr.raiseModbusError(e)
        return response

    def _modbus_write_register(self, address: int, value: int, slave: int) -> int:
        try:
            response = self._rs485Client.write_register(address=address, value=value, slave=slave)
        except ModbusException as e:
            self._errorMgr.raiseModbusError(e)
        return response

    def _modbus_read_coils(self, address: int, slave: int, count: int=1) -> int:
        try:
            response = self._rs485Client.read_coils(address=address, count=count, slave=slave)
        except ModbusException as e:
            self._errorMgr.raiseModbusError(e)
        return response

    def _modbus_write_coil(self, address: int, value: int, slave: int) -> int:
        try:
            response = self._rs485Client.write_coil(address=address, value=value, slave=slave)
        except ModbusException as e:
            self._errorMgr.raiseModbusError(e)
        return response
