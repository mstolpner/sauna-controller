from configobj import ConfigObj
import atexit
import os


class SaunaContext:
    # Default settings
    _saunaSensorsDeviceId = 1
    _relayModuleDeviceId = 2
    _fanControlModuleDeviceId = 3
    _hotRoomTargetTempF = 190
    _coolingGracePeriod = 60  # seconds
    _lowerHotRoomTempThreshold = 5
    _upperHotRoomTempThreshold = 0
    _heaterHealthWarmUpTime = 300
    _heaterHealthCoolDownTime = 1200
    _maxHotRoomTempF = 240
    _targetTempPresetMedium = 180
    _targetTempPresetHigh = 200
    _rs485SerialPort = '/dev/ttyAMA0'
    _rs485SerialBaudRate = 9600
    _rs485Timeout = 0.3
    _rs485Retries = 3
    _fanSpeedPct = 100
    _numberOfFans = 2
    _leftFanOnStatus = False
    _rightFanOnStatus = True
    _hotRoomLightAlwaysOn = False
    _hotRoomLightOn = False
    _screenWidth = 800
    _screenHeight = 1280
    _screenRotation = 270
    _fanRunningTimeAfterSaunaOffHrs = 0.5
    # Dependencies
    _configObj = None
    _configFileName = 'sauna.ini'
    # Runtime-only, not saved to config
    _isSaunaOn = False
    _isHeaterOn = False
    _hotRoomTempF = 20
    _hotRoomHumidity = 50

    def __init__(self):
        iniFileExists = os.path.exists(self._configFileName)
        self._configObj = ConfigObj(self._configFileName)
        if not iniFileExists:
            self.setDefaultSettings()
        # Save configuration on exit
        atexit.register(self._onExit)

    def setDefaultSettings(self):
        self._configObj['rs485'] = {}
        self._configObj['rs485']['sensors_module_device_id'] = self._saunaSensorsDeviceId
        self._configObj['rs485']['relay_module_device_id'] = self._relayModuleDeviceId
        self._configObj['rs485']['fan_module_device_id'] = self._fanControlModuleDeviceId
        self._configObj['rs485']['serial_port_name'] = self._rs485SerialPort
        self._configObj['rs485']['serial_baud_rate'] = self._rs485SerialBaudRate
        self._configObj['rs485']['serial_timeout'] = self._rs485Timeout
        self._configObj['rs485']['serial_retries'] = self._rs485Retries
        self._configObj['hot_room_temp_control'] = {}
        self._configObj['hot_room_temp_control']['target_temp_f'] = self._hotRoomTargetTempF
        self._configObj['hot_room_temp_control']['cooling_grace_period'] = self._coolingGracePeriod
        self._configObj['hot_room_temp_control']['lower_hot_room_temp_threshold_f'] = self._lowerHotRoomTempThreshold
        self._configObj['hot_room_temp_control']['upper_hot_room_temp_threshold_f'] = self._upperHotRoomTempThreshold
        self._configObj['hot_room_temp_control']['heater_health_warmup_time'] = self._heaterHealthWarmUpTime
        self._configObj['hot_room_temp_control']['heater_health_cooldown_time'] = self._heaterHealthCoolDownTime
        self._configObj['hot_room_temp_control']['max_temp_f'] = self._maxHotRoomTempF
        self._configObj['hot_room_temp_control']['target_temp_preset_medium'] = self._targetTempPresetMedium
        self._configObj['hot_room_temp_control']['target_temp_preset_high'] = self._targetTempPresetHigh
        self._configObj['fan_control'] = {}
        self._configObj['fan_control']['fan_speed_pct'] = self._fanSpeedPct
        self._configObj['fan_control']['number_of_fans'] = self._numberOfFans
        self._configObj['fan_control']['left_fan_on_status'] = self._leftFanOnStatus
        self._configObj['fan_control']['right_fan_on_status'] = self._rightFanOnStatus
        self._configObj['fan_control']['running_time_after_sauna_off_hrs'] = self._fanRunningTimeAfterSaunaOffHrs
        self._configObj['hot_room_control'] = {}
        self._configObj['hot_room_control']['hot_room_light_always_on'] = self._hotRoomLightAlwaysOn
        self._configObj['appearance'] = {}
        self._configObj['appearance']['screen_width'] = self._screenWidth
        self._configObj['appearance']['screen_height'] = self._screenHeight
        self._configObj['appearance']['screen_rotation'] = self._screenRotation

    # Save configuration on exit
    def _onExit(self):
        self._configObj.write()

    def isSaunaOn(self) -> bool:
        return self._isSaunaOn

    def isSaunaOff(self) -> bool:
        return not self._isSaunaOn
    
    def turnSaunaOn(self) -> None:
        self._isSaunaOn = True
    
    def turnSaunaOff(self) -> None:
        self._isSaunaOn = False

    def turnSaunaOnOff(self, state: bool) -> None:
        self._isSaunaOn = state

    def isHeaterOn(self) -> bool:
        return self._isHeaterOn

    def setHeaterOn(self) -> None:
        self._isHeaterOn = True

    def setHeaterOff(self) -> None:
        self._isHeaterOn = False

    def getSaunaSensorsDeviceId(self) -> int:
        return self._configObj['rs485'].as_int('sensors_module_device_id')

    def setSaunaSensorsDeviceId(self, saunaSensorsDeviceId: int) -> None:
        self._configObj['rs485']['sensors_module_device_id'] = saunaSensorsDeviceId

    def getRelayModuleDeviceId(self) -> int:
        return self._configObj['rs485'].as_int('relay_module_device_id')

    def setRelayModuleDeviceId(self, relayModuleDeviceId: int) -> None:
        self._configObj['rs485']['relay_module_device_id'] = relayModuleDeviceId

    def getFanControlModuleDeviceId(self) -> int:
        return self._configObj['rs485'].as_int('fan_module_device_id')

    def setFanControlModuleDeviceId(self, fanControlModuleDeviceId: int) -> None:
        self._configObj['rs485']['fan_module_device_id'] = fanControlModuleDeviceId

    def getRs485SerialPort(self) -> str:
        return self._configObj['rs485']['serial_port_name']

    def setRs485SerialPort(self, rs485SerialPort: str) -> None:
        self._configObj['rs485']['serial_port_name'] = rs485SerialPort

    def getRs485SerialBaudRate(self) -> int:
        return self._configObj['rs485'].as_int('serial_baud_rate')

    def setRs485SerialBaudRate(self, rs485SerialBaudRate: int) -> None:
        self._configObj['rs485']['serial_baud_rate'] = rs485SerialBaudRate

    def getRs485SerialTimeout(self) -> float:
        try:
            return self._configObj['rs485'].as_float('serial_timeout')
        except KeyError:
            self.setRs485SerialTimeout(self._rs485Timeout)
            return self._configObj['rs485'].as_float('serial_timeout')

    def setRs485SerialTimeout(self, rs485SerialTimeout: float) -> None:
        self._configObj['rs485']['serial_timeout'] = rs485SerialTimeout

    def getRs485SerialRetries(self) -> int:
        try:
            return self._configObj['rs485'].as_int('serial_retries')
        except KeyError:
            self.setRs485SerialRetries(self._rs485Retries)
            return self._configObj['rs485'].as_int('serial_retries')

    def setRs485SerialRetries(self, rs485SerialRetries: int) -> None:
        self._configObj['rs485']['serial_retries'] = rs485SerialRetries

    def getHotRoomTargetTempF(self) -> int:
        return self._configObj['hot_room_temp_control'].as_int('target_temp_f')

    def setHotRoomTargetTempF(self, targetTemperatureF: int) -> None:
        self._configObj['hot_room_temp_control']['target_temp_f'] = targetTemperatureF

    def getCoolingGracePeriod(self) -> int:
        return self._configObj['hot_room_temp_control'].as_int('cooling_grace_period')

    def setCoolingGracePeriod(self, coolingGracePeriod: int) -> None:
        self._configObj['hot_room_temp_control']['cooling_grace_period'] = coolingGracePeriod

    def getLowerHotRoomTempThresholdF(self) -> int:
        return self._configObj['hot_room_temp_control'].as_int('lower_hot_room_temp_threshold_f')

    def setLowerHotRoomTempThresholdF(self, thresholdTempF: int) -> None:
        self._configObj['hot_room_temp_control']['lower_hot_room_temp_threshold_f'] = thresholdTempF

    def getUpperHotRoomTempThresholdF(self) -> int:
        return self._configObj['hot_room_temp_control'].as_int('upper_hot_room_temp_threshold_f')

    def setUpperHotRoomTempThresholdF(self, thresholdTempF: int) -> None:
        self._configObj['hot_room_temp_control']['upper_hot_room_temp_threshold_f'] = thresholdTempF

    def getHeaterHealthWarmUpTime(self) -> int:
        return self._configObj['hot_room_temp_control'].as_int('heater_health_warmup_time')

    def setLHeaterHealthWarmupTime(self, warmupTime: int) -> None:
        self._configObj['hot_room_temp_control']['heater_health_warmup_time'] = warmupTime

    def getHeaterHealthCooldownTime(self) -> int:
        return self._configObj['hot_room_temp_control'].as_int('heater_health_cooldown_time')

    def setHeaterHealthCooldownTime(self, cooldownTime: int) -> None:
        self._configObj['hot_room_temp_control']['heater_health_cooldown_time'] = cooldownTime

    def getHotRoomMaxTempF(self) -> int:
        return self._configObj['hot_room_temp_control'].as_int('max_temp_f')

    def setHotRoomMaxTempF(self, maxTempF: int) -> None:
        self._configObj['hot_room_temp_control']['max_temp_f'] = maxTempF

    def getFanSpeedPct(self) -> int:
        return self._configObj['fan_control'].as_int('fan_speed_pct')

    def setFanSpeedPct(self, fanSpeedPct: int) -> None:
        self._configObj['fan_control']['fan_speed_pct'] = int(fanSpeedPct)

    def getNumberOfFans(self) -> int:
        return self._configObj['fan_control'].as_int('number_of_fans')

    def setNumberOfFans(self, numberOfFans: int) -> None:
        self._configObj['fan_control']['number_of_fans'] = numberOfFans

    def getRightFanOnStatus(self) -> bool:
        return self._configObj['fan_control'].as_bool('right_fan_on_status')

    def setRightFanOnStatus(self, status: bool) -> None:
        self._configObj['fan_control']['right_fan_on_status'] = status

    def getLeftFanOnStatus(self) -> bool:
        return self._configObj['fan_control'].as_bool('left_fan_on_status')

    def setLeftFanOnStatus(self, status: bool) -> None:
        self._configObj['fan_control']['left_fan_on_status'] = status

    def getHotRoomTempF(self) -> float:
        """Get current hot room temperature in Fahrenheit (runtime-only, not persisted)"""
        return self._hotRoomTempF

    def setHotRoomTempF(self, tempF: float) -> None:
        """Set current hot room temperature in Fahrenheit (runtime-only, not persisted)"""
        self._hotRoomTempF = tempF

    def getHotRoomHumidity(self) -> float:
        """Get current hot room humidity percentage (runtime-only, not persisted)"""
        return self._hotRoomHumidity

    def setHotRoomHumidity(self, humidity: float) -> None:
        """Set current hot room humidity percentage (runtime-only, not persisted)"""
        self._hotRoomHumidity = humidity

    def getTargetTempPresetMedium(self) -> int:
        return self._configObj['hot_room_temp_control'].as_int('target_temp_preset_medium')

    def setTargetTempPresetMedium(self, tempF: int) -> None:
        self._configObj['hot_room_temp_control']['target_temp_preset_medium'] = tempF

    def getTargetTempPresetHigh(self) -> int:
        return self._configObj['hot_room_temp_control'].as_int('target_temp_preset_high')

    def setTargetTempPresetHigh(self, tempF: int) -> None:
        self._configObj['hot_room_temp_control']['target_temp_preset_high'] = tempF

    def getHotRoomLightAlwaysOn(self) -> bool:
        return self._configObj['hot_room_control'].as_bool('hot_room_light_always_on')

    def setHotRoomLightAlwaysOn(self, value: bool) -> None:
        self._configObj['hot_room_control']['hot_room_light_always_on'] = value


    def isHotRoomLightOn(self) -> bool:
        return self._hotRoomLightOn

    def setHotRoomLightOnOff(self, value: bool) -> None:
        self._hotRoomLightOn = value

    def getScreenWidth(self) -> int:
        try:
            return self._configObj['appearance'].as_int('screen_width')
        except KeyError:
            self.setScreenWidth(self._screenWidth)
            return self._configObj['appearance'].as_int('screen_width')

    def setScreenWidth(self, width: int) -> None:
        if 'appearance' not in self._configObj:
            self._configObj['appearance'] = {}
        self._configObj['appearance']['screen_width'] = width

    def getScreenHeight(self) -> int:
        try:
            return self._configObj['appearance'].as_int('screen_height')
        except KeyError:
            self.setScreenHeight(self._screenHeight)
            return self._configObj['appearance'].as_int('screen_height')

    def setScreenHeight(self, height: int) -> None:
        if 'appearance' not in self._configObj:
            self._configObj['appearance'] = {}
        self._configObj['appearance']['screen_height'] = height

    def getScreenRotation(self) -> int:
        try:
            return self._configObj['appearance'].as_int('screen_rotation')
        except KeyError:
            self.setScreenRotation(self._screenRotation)
            return self._configObj['appearance'].as_int('screen_rotation')

    def setScreenRotation(self, rotation: int) -> None:
        if 'appearance' not in self._configObj:
            self._configObj['appearance'] = {}
        self._configObj['appearance']['screen_rotation'] = rotation

    def getFanRunningTimeAfterSaunaOffHrs(self) -> int:
        try:
            return self._configObj['fan_control'].as_int('running_time_after_sauna_off_hrs')
        except KeyError:
            self.setFanRunningTimeAfterSaunaOffHrs(self._fanRunningTimeAfterSaunaOffHrs)
            return self._configObj['fan_control'].as_float('running_time_after_sauna_off_hrs')

    def setFanRunningTimeAfterSaunaOffHrs(self, hours: int) -> None:
        self._configObj['fan_control']['running_time_after_sauna_off_hrs'] = int(hours)
