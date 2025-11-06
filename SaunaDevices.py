import asyncio
import time
import logging
from pymodbus.client import AsyncModbusSerialClient
from pymodbus.exceptions import ModbusException
from ErrorManager import ErrorManager
from SaunaContext import SaunaContext
from Timer import Timer


class ModbusResponseError():
    def isError(self):
        return True


class SaunaDevices:

    # Sauna Context Manager
    _ctx = None

    # Configure logging for asyncio
    logging.getLogger('asyncio').setLevel(logging.WARNING)

    # Sensor Module Configuration
    _lastHotRoomTemperatureC = 0
    _lastHotRoomHumidity = 0

    # Relay Module Configuration
    _lastFanRelayStatus = [False, False]
    _lastHotRoomLightOnStatus = False

    # Fan Module Configuration
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

    # Fan Timer
    _fanAccelerationTimer = None

    # Prior Fan states
    _leftFanPriorState = False
    _rightFanPriorState = False


    def __init__(self, ctx: SaunaContext, errorMgr: ErrorManager):
        # Set modbus Logging Level
        pymodbus_logger = logging.getLogger('pymodbus')
        pymodbus_logger.setLevel(logging.WARN)
        # Dependencies
        self._ctx = ctx
        self._errorMgr = errorMgr
        # Create persistent event loop for async operations
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        # Initialize Hot Room Light
        self._setRelayStatus(self._ctx.getHotRoomLightCoilAddr(), self._ctx.getHotRoomLightAlwaysOn() or self._ctx.isSaunaOn())
        # Initialize Fans
        if self.getNumberOfFans() != self._ctx.getNumberOfFans():
            self.setNumberOfFans(self._ctx.getNumberOfFans())
        self.setFanSpeed(self._ctx.getFanSpeedPct())
        # Fans are off initially and get managed by the SaunaController
        self._setFanRelayStatus(self._ctx.getRightFanRelayCoilAddr(), False)
        self._setFanRelayStatus(self._ctx.getLeftFanRelayCoilAddr(), False)
        # These 2 functions will populate _lastFanRelayStatus[]
        self._getFanRelayStatus(self._ctx.getRightFanRelayCoilAddr())
        self._getFanRelayStatus(self._ctx.getLeftFanRelayCoilAddr())
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
        # Initialize hot room light
        self.turnHotRoomLightOnOff(self._ctx.getHotRoomLightAlwaysOn() or self._ctx.isSaunaOn())
        # Initialize fan timer to prevent false errors during fan acceleration
        self._fanAccelerationTimer = Timer(10)
        # Release resources on exit
        import atexit
        atexit.register(self._onExit)

    # Release resources on exit
    def _onExit(self):
        # Give it a chance to turn equipment off
        time.sleep(10)
        if self._client:
            self._loop.run_until_complete(self._client.close())
        if self._loop:
            self._loop.close()

    # ---------------------------------------- Sauna Sensors ---------------------------------------

    def getHotRoomTemperature(self, system='F') -> int:
        response=self._modbus_read_holding_registers(self._ctx.getTempSensorAddr(), self._ctx.getSaunaSensorsDeviceId())
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
        response=self._modbus_read_holding_registers(self._ctx.getHumiditySensorAddr(), self._ctx.getSaunaSensorsDeviceId())
        if response.isError():
            self._errorMgr.raiseSensorModuleError('Cannot Read Humidity Sensor.')
        else:
            self._errorMgr.eraseSensorModuleError()
            self._lastHotRoomHumidity = response.registers[0] / 10
        return round(self._lastHotRoomHumidity)

    def getRestingRoomTemp(self, system='F') -> int:
        response=self._modbus_read_holding_registers(self._ctx.getFanModuleRoomTempAddr(), self._ctx.getSaunaSensorsDeviceId())
        if response.isError():
            self._errorMgr.raiseFanModuleError('Cannot get Resting Room Temperature.')
        else:
            self._errorMgr.eraseFanModuleError()
            self._lastRestingRoomTemp = response.registers[0] - 40
        if system == 'F':
            return round((self._lastRestingRoomTemp * 9 / 5) + 32)
        return self._lastRestingRoomTemp


    # ---------------------------------- Sauna Heater Functions ----------------------------------

    def isHeaterOn(self) -> bool:
        response = self._modbus_read_coils(self._ctx.getHeaterRelayCoilAddr(), self._ctx.getRelayModuleDeviceId())
        if response.isError():
            self._errorMgr.raiseRelayModuleError('Cannot get Heater Status.')
        else:
            self._errorMgr.eraseRelayModuleError()
            self._lastHeaterOnStatus = response.bits[self._ctx.getHeaterRelayCoilAddr()]
        return self._lastHeaterOnStatus

    def isHeaterOff(self) -> bool:
        return not self.isHeaterOn()

    def setHeaterRelay(self, status: bool) -> None:
        response = self._modbus_write_coil(self._ctx.getHeaterRelayCoilAddr(), status, self._ctx.getRelayModuleDeviceId())
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
        self._ctx.setHeaterOn()

    def turnHeaterOff(self) -> None:
        self.setHeaterRelay(False)
        self._ctx.setHeaterOff()

    def getHotRoomLightStatus(self) -> bool:
        response = self._modbus_read_coils(self._ctx.getHotRoomLightCoilAddr(), self._ctx.getRelayModuleDeviceId())
        if response.isError():
            self._errorMgr.raiseRelayModuleError('Cannot get Hot Room Light status.')
        else:
            self._errorMgr.eraseRelayModuleError()
            self._lastHotRoomLightOnStatus = response.bits[self._ctx.getHotRoomLightCoilAddr()]
        return self._lastHotRoomLightOnStatus

    def turnHotRoomLightOnOff(self, status: bool) -> None:
        response = self._modbus_write_coil(self._ctx.getHotRoomLightCoilAddr(), status, self._ctx.getRelayModuleDeviceId())
        if response.isError():
            self._errorMgr.raiseRelayModuleError('Cannot Turn the Hot Room Light On or Off.')
        else:
            self._errorMgr.eraseRelayModuleError()
            self._lastHotRoomLightOnStatus = status


    # ------------------------------------- Vent Fans Functions -------------------------------------

    def _setRelayStatus(self, relayCoilId: int, state: bool) -> None:
        response = self._modbus_write_coil(relayCoilId, state, self._ctx.getRelayModuleDeviceId())
        if response.isError():
            self._errorMgr.raiseRelayModuleError('Cannot Manipulate Relays.')
        else:
            self._errorMgr.eraseRelayModuleError()

    def _getFanRelayStatus(self, fanCoilId: int) -> bool:
        response = self._modbus_read_coils(fanCoilId, self._ctx.getRelayModuleDeviceId())
        if response.isError():
            self._errorMgr.raiseRelayModuleError('Cannot Get Fan Status.')
        else:
            self._errorMgr.eraseRelayModuleError()
            self._lastFanRelayStatus[fanCoilId - 2] = response.bits[0]
        return self._lastFanRelayStatus[fanCoilId - 2]

    def _setFanRelayStatus(self, fanCoilId: int, state: bool) -> None:
        response = self._modbus_write_coil(fanCoilId, state, self._ctx.getRelayModuleDeviceId())
        if response.isError():
            self._errorMgr.raiseRelayModuleError('Cannot Turn a Fan On or Off.')
        else:
            self._errorMgr.eraseRelayModuleError()
            self._lastFanRelayStatus[fanCoilId - 2] = state

    # fanId - either _rightFanId or _leftFanId
    def _getFanStatus(self, fanId) -> bool:
        # low 4 bits correspond to 4 fans, from right to left, the most right bit corresponds to fan 1,
        # 0 means the fan stops and 1 means the fan is running
        response = self._modbus_read_holding_registers(self._ctx.getFanStatusAddr(), self._ctx.getFanControlModuleDeviceId())
        if response.isError():
            self._errorMgr.raiseFanModuleError('Cannot Get Fan Status from Fan Module.RelayModule')
        else:
            self._errorMgr.eraseFanModuleError()
            self._lastFanStatus[fanId-1] = (response.registers[0] & fanId) > 0
        return self._lastFanStatus[fanId-1]

    def _getFanSpeedRpm(self, fanId: int) -> int:
        response = self._modbus_read_holding_registers(6 + fanId, self._ctx.getFanControlModuleDeviceId())
        if response.isError():
            self._errorMgr.raiseFanModuleError('Cannot Get Fan Speed.')
        else:
            self._errorMgr.eraseFanModuleError()
            self._lastFanSpeed[fanId - 1] = response.registers[0]
        return self._lastFanSpeed[fanId - 1]

    # Sets speed for all fans. 0% ... 100%. Most fans will start running at 10% or more
    def setFanSpeed(self, speedPct: int) -> None:
        response = self._modbus_write_register(self._ctx.getFanSpeedAddr(), speedPct, self._ctx.getFanControlModuleDeviceId())
        if response.isError():
            self._errorMgr.raiseFanModuleError('Cannot Change Fan Speed.')
        else:
            self._errorMgr.eraseFanModuleError()

    def getLeftFanSpeedRpm(self) -> int:
        return self._getFanSpeedRpm(self._leftFanId)

    def getRightFanSpeedRpm(self) -> int:
        return self._getFanSpeedRpm(self._rightFanId)

    def isRightFanOn(self) -> bool:
        return self._getFanRelayStatus(self._ctx.getRightFanRelayCoilAddr())

    def isRightFanOff(self) -> bool:
        return not self.isRightFanOn()

    def isLeftFanOn(self) -> bool:
        return self._getFanRelayStatus(self._ctx.getLeftFanRelayCoilAddr())

    def isLeftFanOff(self) -> bool:
        return not self.isLeftFanOn()

    def turnLeftFanOn(self) -> None:
        self.turnLeftFanOnOff(True)

    def turnLeftFanOff(self) -> None:
        self.turnLeftFanOnOff(False)

    def turnLeftFanOnOff(self, state: bool) -> None:
        self._setFanRelayStatus(self._ctx.getLeftFanRelayCoilAddr(), state)
        if state and not self._leftFanPriorState:
            self._fanAccelerationTimer.start()
        self._leftFanPriorState = state

    def turnRightFanOn(self) -> None:
        self.turnRightFanOnOff(True)

    def turnRightFanOff(self) -> None:
        self.turnRightFanOnOff(False)

    def turnRightFanOnOff(self, state: bool) -> None:
        self._setFanRelayStatus(self._ctx.getRightFanRelayCoilAddr(), state)
        if state and not self._rightFanPriorState:
            self._fanAccelerationTimer.start()
        self._rightFanPriorState = state

    def getNumberOfFans(self) -> int:
        response = self._modbus_read_holding_registers(self._ctx.getNumberOfFansAddr(), self._ctx.getFanControlModuleDeviceId())
        if response.isError():
            self._errorMgr.raiseFanModuleError('Cannot Get Number of Fans.')
            return self._ctx.getNumberOfFans()
        else:
            self._errorMgr.eraseFanModuleError()
            return response.registers[0]

    def setNumberOfFans(self, nFans: int) -> None:
        response = self._modbus_write_register(self._ctx.getNumberOfFansAddr(), nFans, self._ctx.getFanControlModuleDeviceId())
        if response.isError():
            self._errorMgr.raiseFanModuleError('Cannot Set Number of Fans.')
        else:
            self._errorMgr.eraseFanModuleError()

    def _checkFanFaultStatus(self, fanId: int) -> bool:
        # Give fan a chance to gain speed
        if self._fanAccelerationTimer.isRunning():
            return False
        response = self._modbus_read_holding_registers(self._ctx.getFanFaultStatusAddr(), self._ctx.getFanControlModuleDeviceId())
        if response.isError():
            self._errorMgr.raiseFanModuleError('Cannot Read Fan Status.')
            return True
        else:
            self._errorMgr.eraseFanModuleError()
            # Bit set to 0 corresponds to error
            return (response.registers[0] & fanId) == 0

    def isLeftFanOk(self) -> bool:
        # Fan controller reports fan staus failed if the fan is off managed by a relay
        a = self._checkFanFaultStatus(self._leftFanId)
        return not self._ctx.isLeftFanEnabled() or not self._checkFanFaultStatus(self._leftFanId)

    def isRightFanOk(self) -> bool:
        # Fan controller reports fan staus failed if the fan is off managed by a relay
        return not self._ctx.isRightFanEnabled() or not self._checkFanFaultStatus(self._rightFanId)

    def _resetFanModuleGovernor(self) -> None:
        response = self._modbus_write_register(self._ctx.getFanModuleGovernorAddr(),
                                               self._ctx.getFanModuleResetGovernorValue(),
                                               self._ctx.getFanControlModuleDeviceId())
        if response.isError():
            self._errorMgr.raiseFanModuleError('Cannot Reset Fan Module.')
        else:
            self._errorMgr.eraseFanModuleError()


    # ----------------------------------- Modbus Client Functions -------------------------------------

    _client: AsyncModbusSerialClient = None

    def _modbus_read_holding_registers(self, address: int, slave: int, count: int=1):
        async def _read():
            try:
                if self._client is None:
                    self._client = AsyncModbusSerialClient(port=self._ctx.getModbusSerialPort(),
                                                           baudrate=self._ctx.getModbusSerialBaudRate(),
                                                           timeout=self._ctx.getModbusSerialTimeout(),
                                                           retries=self._ctx.getModbusSerialRetries())
                    await self._client.connect()
                response = await self._client.read_holding_registers(address, count=1, slave=slave)
                return response
            except ModbusException as e:
                self._errorMgr.raiseModbusError(e)
                return ModbusResponseError()
        return self._loop.run_until_complete(_read())

    def _modbus_write_register(self, address: int, value: int, slave: int):
        async def _read():
            try:
                if self._client is None:
                    self._client = AsyncModbusSerialClient(port=self._ctx.getModbusSerialPort(),
                                                    baudrate=self._ctx.getModbusSerialBaudRate(),
                                                    timeout=self._ctx.getModbusSerialTimeout(),
                                                    retries=self._ctx.getModbusSerialRetries())
                    await self._client.connect()
                response = await self._client.write_register(address=address, value=value, slave=slave)
                return response
            except ModbusException as e:
                self._errorMgr.raiseModbusError(e)
                return ModbusResponseError()
        return self._loop.run_until_complete(_read())

    def _modbus_read_coils(self, address: int, slave: int, count: int=1):
        async def _read():
            try:
                if self._client is None:
                    self._client = AsyncModbusSerialClient(port=self._ctx.getModbusSerialPort(),
                                                    baudrate=self._ctx.getModbusSerialBaudRate(),
                                                    timeout=self._ctx.getModbusSerialTimeout(),
                                                    retries=self._ctx.getModbusSerialRetries())
                    await self._client.connect()
                response = await self._client.read_coils(address=address, count=count, slave=slave)
                return response
            except ModbusException as e:
                self._errorMgr.raiseModbusError(e)
                return ModbusResponseError()
        return self._loop.run_until_complete(_read())


    def _modbus_write_coil(self, address: int, value: bool, slave: int):
        async def _read():
            try:
                if self._client is None:
                    self._client = AsyncModbusSerialClient(port=self._ctx.getModbusSerialPort(),
                                                    baudrate=self._ctx.getModbusSerialBaudRate(),
                                                    timeout=self._ctx.getModbusSerialTimeout(),
                                                    retries=self._ctx.getModbusSerialRetries())
                    await self._client.connect()
                response = await self._client.write_coil(address=address, value=value, slave=slave)
                return response
            except ModbusException as e:
                self._errorMgr.raiseModbusError(e)
                return ModbusResponseError()
        return self._loop.run_until_complete(_read())