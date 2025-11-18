import logging
from typing import Any, Optional
from configobj import ConfigObj
import os
import subprocess
import secrets
from Timer import Timer


class SaunaContext:
    _logger: logging.Logger = logging.getLogger('sauna-controller')
    # Modbus Serial Port Default Settings
    _modbusSerialPort = '/dev/ttyAMA0'
    _modbusSerialBaudRate: int = 9600
    _modbusSerialTimeout: float = 0.3
    _modbusSerialRetries: int = 3
    # Modbus Device IDs
    _saunaSensorsDeviceId: int = 1
    _relayModuleDeviceId: int = 2
    _fanControlModuleDeviceId: int = 3
    # Modbus Register Addresses
    _tempSensorAddr: int = 1
    _humiditySensorAddr: int = 0
    _heaterRelayCoilAddr: int = 0
    _hotRoomLightCoilAddr: int = 1
    _rightFanRelayCoilAddr: int = 2
    _leftFanRelayCoilAddr: int = 3
    _fanModuleRoomTempAddr: int = 0
    _fanStatusAddr: int = 1
    _fanSpeedAddr: int = 3
    _numberOfFansAddr: int = 6
    _fanFaultStatusAddr: int = 14
    _fanModuleGovernorAddr: int = 32
    _fanModuleResetGovernorValue: int = 170
    # Heater Default Settings
    _hotRoomTargetTempF: int = 190
    _coolingGracePeriodMin: int = 5
    _lowerHotRoomTempThreshold: int = 5
    _upperHotRoomTempThreshold: int = 0
    _heaterHealthWarmUpTimeMin: int = 10
    _heaterHealthCoolDownTimeMin: int = 20
    _heaterMaxSafeRuntimeMin: int = 240
    _maxHotRoomTempF: int = 240
    _targetTempPresetMedium: int = 180
    _targetTempPresetHigh: int = 200
    _heaterCycleOnPeriodMin: int = 30
    _heaterCycleOffPeriodMin: int = 15
    # Fan Default Settings
    _fanSpeedPct: int = 100
    _numberOfFans: int = 2
    _fanRunningTimeAfterSaunaOffHrs: float = 4.0
    # Hot Room Light Default Settings
    _hotRoomLightAlwaysOn: bool = False
    _hotRoomLightOn: bool = False
    # Appearance Default Settings
    _displayWidth: int = 800
    _displayHeight: int = 1280
    _displayRotation: int = 270
    _displayDevicePath = "/sys/class/backlight/11-0045"
    _displayBrightness: int = 255
    # System Settings (Web Server, CPU, etc.)
    _httpHost = '0.0.0.0'
    _httpPort: int = 8080
    _cpuWarnTempC: int = 90
    _logLevel: int = logging.WARNING
    _maxSaunaOnTimeHrs: int = 6
    # Authentication Settings
    _webPassword: str = 'sauna123'
    _secretKey: str = None  # Will be generated if not set
    # Dependencies
    _configObj = None
    _configFileName = 'sauna.ini'
    # Runtime-only, not saved to config
    _isSaunaOn = False
    _isHeaterOn = False
    _hotRoomTempF = 20
    _hotRoomHumidity = 50
    _leftFanRpm = 0
    _rightFanRpm = 0
    _leftFanOnStatus = False
    _rightFanOnStatus = True
    _cpuTempC = 0
    # Timers
    _fanAfterSaunaOffTimer: Timer = None
    _saunaOnTimer: Timer = None

    # TODO Split settings screen.
    # TODO Add errors to fan settings.
    def __init__(self):
        iniFileExists = os.path.exists(self._configFileName)
        self._configObj = ConfigObj(self._configFileName)
        if not iniFileExists:
            self._logger.warning('File sauna.ini not found. Creating a new file with default configuration.')
            self.setDefaultSettings()
            self.persist()
        # Set log level from config
        self._logger.setLevel(self.getLogLevel())
        # Initialize timers
        self._fanAfterSaunaOffTimer = Timer(round(self.getFanRunningTimeAfterSaunaOffHrs() * 60 * 60))
        self._saunaOnTimer = Timer(round(self.getMaxSaunaOnTimeHrs() * 60 * 60))

    def getLogger(self) -> logging.Logger:
        return self._logger

    def setDefaultSettings(self):
        self._configObj['modbus'] = {}
        self._configObj['modbus']['sensors_module_device_id'] = self._saunaSensorsDeviceId
        self._configObj['modbus']['relay_module_device_id'] = self._relayModuleDeviceId
        self._configObj['modbus']['fan_module_device_id'] = self._fanControlModuleDeviceId
        self._configObj['modbus']['serial_port_name'] = self._modbusSerialPort
        self._configObj['modbus']['serial_baud_rate'] = self._modbusSerialBaudRate
        self._configObj['modbus']['serial_timeout'] = self._modbusSerialTimeout
        self._configObj['modbus']['serial_retries'] = self._modbusSerialRetries
        self._configObj['modbus']['temp_sensor_addr'] = self._tempSensorAddr
        self._configObj['modbus']['humidity_sensor_addr'] = self._humiditySensorAddr
        self._configObj['modbus']['heater_relay_coil_addr'] = self._heaterRelayCoilAddr
        self._configObj['modbus']['hot_room_light_coil_addr'] = self._hotRoomLightCoilAddr
        self._configObj['modbus']['right_fan_relay_coil_addr'] = self._rightFanRelayCoilAddr
        self._configObj['modbus']['left_fan_relay_coil_addr'] = self._leftFanRelayCoilAddr
        self._configObj['modbus']['fan_module_room_temp_addr'] = self._fanModuleRoomTempAddr
        self._configObj['modbus']['fan_status_addr'] = self._fanStatusAddr
        self._configObj['modbus']['fan_speed_addr'] = self._fanSpeedAddr
        self._configObj['modbus']['number_of_fans_addr'] = self._numberOfFansAddr
        self._configObj['modbus']['fan_fault_status_addr'] = self._fanFaultStatusAddr
        self._configObj['modbus']['fan_module_governor_addr'] = self._fanModuleGovernorAddr
        self._configObj['modbus']['fan_module_reset_governor_value'] = self._fanModuleResetGovernorValue
        self._configObj['hot_room_temp_control'] = {}
        self._configObj['hot_room_temp_control']['target_temp_f'] = self._hotRoomTargetTempF
        self._configObj['hot_room_temp_control']['cooling_grace_period_min'] = self._coolingGracePeriodMin
        self._configObj['hot_room_temp_control']['lower_hot_room_temp_threshold_f'] = self._lowerHotRoomTempThreshold
        self._configObj['hot_room_temp_control']['upper_hot_room_temp_threshold_f'] = self._upperHotRoomTempThreshold
        self._configObj['hot_room_temp_control']['max_temp_f'] = self._maxHotRoomTempF
        self._configObj['hot_room_temp_control']['target_temp_preset_medium'] = self._targetTempPresetMedium
        self._configObj['hot_room_temp_control']['target_temp_preset_high'] = self._targetTempPresetHigh
        self._configObj['fan_control'] = {}
        self._configObj['fan_control']['fan_speed_pct'] = self._fanSpeedPct
        self._configObj['fan_control']['number_of_fans'] = self._numberOfFans
        self._configObj['fan_control']['left_fan_enabled_min'] = self._leftFanOnStatus
        self._configObj['fan_control']['right_fan_enabled_min'] = self._rightFanOnStatus
        self._configObj['fan_control']['running_time_after_sauna_off_hrs'] = self._fanRunningTimeAfterSaunaOffHrs
        self._configObj['hot_room_control'] = {}
        self._configObj['hot_room_control']['hot_room_light_always_on'] = self._hotRoomLightAlwaysOn
        self._configObj['heater_control'] = {}
        self._configObj['heater_control']['heater_health_warmup_time_min'] = self._heaterHealthWarmUpTimeMin
        self._configObj['heater_control']['heater_health_cooldown_time_min'] = self._heaterHealthCoolDownTimeMin
        self._configObj['heater_control']['heater_max_safe_runtime_min'] = self._heaterMaxSafeRuntimeMin
        self._configObj['heater_control']['cycle_on_period_min'] = self._heaterCycleOnPeriodMin
        self._configObj['heater_control']['cycle_off_period_min'] = self._heaterCycleOffPeriodMin
        self._configObj['display'] = {}
        self._configObj['display']['display_width'] = self._displayWidth
        self._configObj['display']['display_height'] = self._displayHeight
        self._configObj['display']['display_rotation'] = self._displayRotation
        self._configObj['display']['display_device_path'] = self._displayDevicePath
        self._configObj['display']['display_brightness'] = self._displayBrightness
        self._configObj['system'] = {}
        self._configObj['system']['http_host'] = self._httpHost
        self._configObj['system']['http_port'] = self._httpPort
        self._configObj['system']['cpu_warn_temp_c'] = self._cpuWarnTempC
        self._configObj['system']['log_level'] = self._logLevel
        self._configObj['system']['max_sauna_on_time_hrs'] = self._maxSaunaOnTimeHrs
        self._configObj['system']['web_password'] = self._webPassword
        self._configObj['system']['secret_key'] = secrets.token_hex(32)

    def persist(self):
        self._configObj.write()
        self._logger.setLevel(self.getLogLevel())

    # ----------------------- Modbus configuration attributes --------------------------

    def _initSection(self, section: str):
        if section not in self._configObj:
            self._configObj[section] = {}

    def _get(self, section: str, key: str, default: Any) -> Any:
        try:
            if type(default) == float:
                return self._configObj[section].as_float(key)
            elif type(default) == int:
                return self._configObj[section].as_int(key)
            elif type(default) == bool:
                return self._configObj[section].as_bool(key)
            elif type(default) == str:
                return self._configObj[section][key]
        except KeyError:
            self._initSection(section)
            self._set(section, key, default)
            return default

    def _set(self, section: str, key: str, value: Any) -> None:
        self._initSection(section)
        self._configObj[section][key] = value
        self.persist()

    # ------------------------ Modbus Configuration -----------------------

    def getSaunaSensorsDeviceId(self) -> int:
        return self._get('modbus', 'sensors_module_device_id', self._saunaSensorsDeviceId)

    def setSaunaSensorsDeviceId(self, saunaSensorsDeviceId: int) -> None:
        self._set('modbus', 'sensors_module_device_id', saunaSensorsDeviceId)

    def getRelayModuleDeviceId(self) -> int:
        return self._get('modbus', 'relay_module_device_id', self._relayModuleDeviceId)

    def setRelayModuleDeviceId(self, relayModuleDeviceId: int) -> None:
        self._set('modbus', 'relay_module_device_id', relayModuleDeviceId)

    def getFanControlModuleDeviceId(self) -> int:
        return self._get('modbus', 'fan_module_device_id', self._fanControlModuleDeviceId)

    def setFanControlModuleDeviceId(self, fanControlModuleDeviceId: int) -> None:
        self._set('modbus', 'fan_module_device_id', fanControlModuleDeviceId)

    def getModbusSerialPort(self) -> str:
        return self._get('modbus', 'serial_port_name', self._modbusSerialPort)

    def setModbusSerialPort(self, modbus_serial_port: str) -> None:
        self._set('modbus', 'serial_port_name', modbus_serial_port)

    def getModbusSerialBaudRate(self) -> int:
        return self._get('modbus', 'serial_baud_rate', self._modbusSerialBaudRate)

    def setModbusSerialBaudRate(self, modbus_serial_baud_rate: int) -> None:
        self._set('modbus', 'serial_baud_rate', modbus_serial_baud_rate)

    def getModbusSerialTimeout(self) -> float:
        return self._get('modbus', 'serial_timeout', self._modbusSerialTimeout)

    def setModbusSerialTimeout(self, modbus_serial_timeout: float) -> None:
        self._set('modbus', 'serial_timeout', modbus_serial_timeout)

    def getModbusSerialRetries(self) -> int:
        return self._get('modbus', 'serial_retries', self._modbusSerialRetries)

    def setModbusSerialRetries(self, modbus_serial_retries: int) -> None:
        self._set('modbus', 'serial_retries', modbus_serial_retries)

    def getTempSensorAddr(self) -> int:
        return self._get('modbus', 'temp_sensor_addr', self._tempSensorAddr)

    def setTempSensorAddr(self, addr: int) -> None:
        self._set('modbus', 'temp_sensor_addr', addr)

    def getHumiditySensorAddr(self) -> int:
        return self._get('modbus', 'humidity_sensor_addr', self._humiditySensorAddr)

    def setHumiditySensorAddr(self, addr: int) -> None:
        self._set('modbus', 'humidity_sensor_addr', addr)

    def getHeaterRelayCoilAddr(self) -> int:
        return self._get('modbus', 'heater_relay_coil_addr', self._heaterRelayCoilAddr)

    def setHeaterRelayCoilAddr(self, coil_addr: int) -> None:
        self._set('modbus', 'heater_relay_coil_addr', coil_addr)

    def getHotRoomLightCoilAddr(self) -> int:
        return self._get('modbus', 'hot_room_light_coil_addr', self._hotRoomLightCoilAddr)

    def setHotRoomLightCoilAddr(self, coil_addr: int) -> None:
        self._set('modbus', 'hot_room_light_coil_addr', coil_addr)

    def getRightFanRelayCoilAddr(self) -> int:
        return self._get('modbus', 'right_fan_relay_coil_addr', self._rightFanRelayCoilAddr)

    def setRightFanRelayCoilAddr(self, coil_addr: int) -> None:
        self._set('modbus', 'right_fan_relay_coil_addr', coil_addr)

    def getLeftFanRelayCoilAddr(self) -> int:
        return self._get('modbus', 'left_fan_relay_coil_addr', self._leftFanRelayCoilAddr)

    def setLeftFanRelayCoilAddr(self, coil_addr: int) -> None:
        self._set('modbus', 'left_fan_relay_coil_addr', coil_addr)

    def getFanModuleRoomTempAddr(self) -> int:
        return self._get('modbus', 'fan_module_room_temp_addr', self._fanModuleRoomTempAddr)

    def setFanModuleRoomTempAddr(self, addr: int) -> None:
        self._set('modbus', 'fan_module_room_temp_addr', addr)

    def getFanStatusAddr(self) -> int:
        return self._get('modbus', 'fan_status_addr', self._fanStatusAddr)

    def setFanStatusAddr(self, addr: int) -> None:
        self._set('modbus', 'fan_status_addr', addr)

    def getFanSpeedAddr(self) -> int:
        return self._get('modbus', 'fan_speed_addr', self._fanSpeedAddr)

    def setFanSpeedAddr(self, addr: int) -> None:
        self._set('modbus', 'fan_speed_addr', addr)

    def getNumberOfFansAddr(self) -> int:
        return self._get('modbus', 'number_of_fans_addr', self._numberOfFansAddr)

    def setNumberOfFansAddr(self, addr: int) -> None:
        self._set('modbus', 'number_of_fans_addr', addr)

    def getFanFaultStatusAddr(self) -> int:
        return self._get('modbus', 'fan_fault_status_addr', self._fanFaultStatusAddr)

    def setFanFaultStatusAddr(self, addr: int) -> None:
        self._set('modbus', 'fan_fault_status_addr', addr)

    def getFanModuleGovernorAddr(self) -> int:
        return self._get('modbus', 'fan_module_governor_addr', self._fanModuleGovernorAddr)

    def setFanModuleGovernorAddr(self, addr: int) -> None:
        self._set('modbus', 'fan_module_governor_addr', addr)

    def getFanModuleResetGovernorValue(self) -> int:
        return self._get('modbus', 'fan_module_reset_governor_value', self._fanModuleResetGovernorValue)

    def setFanModuleResetGovernorValue(self, value: int) -> None:
        self._set('modbus', 'fan_module_reset_governor_value', value)

    # ----------------------- Hot Room Temp Control attributes --------------------------

    def getHotRoomTargetTempF(self) -> int:
        return self._get('hot_room_temp_control', 'target_temp_f', self._targetTempPresetMedium)

    def setHotRoomTargetTempF(self, targetTemperatureF: int) -> None:
        self._set('hot_room_temp_control', 'target_temp_f', targetTemperatureF)

    def getCoolingGracePeriodMin(self) -> int:
        return self._get('hot_room_temp_control', 'cooling_grace_period_min', self._coolingGracePeriodMin)

    def setCoolingGracePeriodMin(self, coolingGracePeriodMin: int) -> None:
        self._set('hot_room_temp_control', 'cooling_grace_period_min', coolingGracePeriodMin)

    def getLowerHotRoomTempThresholdF(self) -> int:
        return self._get('hot_room_temp_control', 'lower_hot_room_temp_threshold_f', self._lowerHotRoomTempThreshold)

    def setLowerHotRoomTempThresholdF(self, thresholdTempF: int) -> None:
        self._set('hot_room_temp_control', 'lower_hot_room_temp_threshold_f', thresholdTempF)

    def getUpperHotRoomTempThresholdF(self) -> int:
        return self._get('hot_room_temp_control', 'upper_hot_room_temp_threshold_f', self._upperHotRoomTempThreshold)

    def setUpperHotRoomTempThresholdF(self, thresholdTempF: int) -> None:
        self._set('hot_room_temp_control', 'upper_hot_room_temp_threshold_f', thresholdTempF)

    def getHotRoomMaxTempF(self) -> int:
        return self._get('hot_room_temp_control', 'max_temp_f', self._maxHotRoomTempF)

    def setHotRoomMaxTempF(self, maxTempF: int) -> None:
        self._set('hot_room_temp_control', 'max_temp_f', maxTempF)

    def getTargetTempPresetMedium(self) -> int:
        return self._get('hot_room_temp_control', 'target_temp_preset_medium', self._targetTempPresetMedium)

    def setTargetTempPresetMedium(self, tempF: int) -> None:
        self._set('hot_room_temp_control', 'target_temp_preset_medium', tempF)

    def getTargetTempPresetHigh(self) -> int:
        return self._get('hot_room_temp_control', 'target_temp_preset_high', self._targetTempPresetHigh)

    def setTargetTempPresetHigh(self, tempF: int) -> None:
        self._set('hot_room_temp_control', 'target_temp_preset_high', tempF)

    # ----------------------- Heater Control attributes --------------------------

    def getHeaterHealthWarmUpTimeMin(self) -> int:
        return self._get('heater_control', 'heater_health_warmup_time_min', self._heaterHealthWarmUpTimeMin)

    def setHeaterHealthWarmupTimeMin(self, warmupTimeMin: int) -> None:
        self._set('heater_control', 'heater_health_warmup_time_min', warmupTimeMin)

    def getHeaterHealthCooldownTimeMin(self) -> int:
        return self._get('heater_control', 'heater_health_cooldown_time_min', self._heaterHealthCoolDownTimeMin)

    def setHeaterHealthCooldownTimeMin(self, cooldownTimeMin: int) -> None:
        self._set('heater_control', 'heater_health_cooldown_time_min', cooldownTimeMin)

    def getHeaterMaxSafeRuntimeMin(self) -> int:
        return self._get('heater_control', 'heater_max_safe_runtime_min', self._heaterMaxSafeRuntimeMin)

    def setHeaterMaxSafeRuntimeMin(self, value: int) -> None:
        self._set('heater_control', 'heater_max_safe_runtime_min', value)

    def getHeaterCycleOnPeriodMin(self) -> int:
        return self._get('heater_control', 'cycle_on_period_min', self._heaterCycleOnPeriodMin)

    def setHeaterCycleOnPeriodMin(self, value: int) -> None:
        self._set('heater_control', 'cycle_on_period_min', value)

    def getHeaterCycleOffPeriodMin(self) -> int:
        return self._get('heater_control', 'cycle_off_period_min', self._heaterCycleOffPeriodMin)

    def setHeaterCycleOffPeriodMin(self, value: int) -> None:
        self._set('heater_control', 'cycle_off_period_min', value)

    # ----------------------- Hot Room Control attributes --------------------------

    def getHotRoomLightAlwaysOn(self) -> bool:
        return self._get('hot_room_control', 'hot_room_light_always_on', self._hotRoomLightAlwaysOn)

    def setHotRoomLightAlwaysOn(self, value: bool) -> None:
        self._set('hot_room_control', 'hot_room_light_always_on', value)

    # ----------------------- Fan Control attributes --------------------------

    def getFanSpeedPct(self) -> int:
        return self._get('fan_control', 'fan_speed_pct', self._fanSpeedPct)

    def setFanSpeedPct(self, fanSpeedPct: int) -> None:
        self._set('fan_control', 'fan_speed_pct', fanSpeedPct)

    def getNumberOfFans(self) -> int:
        return self._get('fan_control', 'number_of_fans', self._numberOfFans)

    def setNumberOfFans(self, numberOfFans: int) -> None:
        self._set('fan_control', 'number_of_fans', numberOfFans)

    def isRightFanEnabled(self) -> bool:
        return self._get('fan_control', 'right_fan_enabled', self._rightFanOnStatus)

    def setRightFanEnabled(self, status: bool) -> None:
        self._set('fan_control', 'right_fan_enabled', status)

    def isLeftFanEnabled(self) -> bool:
        return self._get('fan_control', 'left_fan_enabled', self._leftFanOnStatus)

    def setLeftFanEnabled(self, status: bool) -> None:
        self._set('fan_control', 'left_fan_enabled', status)

    def getFanRunningTimeAfterSaunaOffHrs(self) -> float:
        return self._get('fan_control', 'running_time_after_sauna_off_hrs', self._fanRunningTimeAfterSaunaOffHrs)

    def setFanRunningTimeAfterSaunaOffHrs(self, hours: float) -> None:
        self._set('fan_control', 'running_time_after_sauna_off_hrs', hours)
        self._fanAfterSaunaOffTimer.setTimeInterval(self.getFanRunningTimeAfterSaunaOffHrs() * 60 * 60)

    # ----------------------- Display attributes --------------------------

    def getScreenWidth(self) -> int:
        return self._get('display', 'display_width', self._displayWidth)

    def setScreenWidth(self, width: int) -> None:
        self._set('display', 'display_width', width)

    def getScreenHeight(self) -> int:
        return self._get('display', 'display_height', self._displayHeight)

    def setScreenHeight(self, height: int) -> None:
        self._set('display', 'display_height', height)

    def getScreenRotation(self) -> int:
        return self._get('display', 'display_rotation', self._displayRotation)

    def setScreenRotation(self, rotation: int) -> None:
        self._set('display', 'display_rotation', rotation)

    def getDisplayDevicePath(self) -> str:
        return self._get('display', 'display_device_path', self._displayDevicePath)

    def getDisplayDeviceBrightnessPath(self):
        path = self.getDisplayDevicePath()
        if path[-1] == '/':
            path = path[:-1]
        return path + '/brightness'

    def setDisplayDevicePath(self, path: str) -> None:
        self._set('display', 'display_device_path', path)

    def getDisplayBrightness(self) -> int:
        return self._get('display', 'display_brightness', self._displayBrightness)

    def setDisplayBrightness(self, brightness: int) -> None:
        self._set('display', 'display_brightness', brightness)
        subprocess.getstatusoutput(f'echo {brightness} > {self.getDisplayDeviceBrightnessPath()}')


    # -------------------------- System Settings --------------------------------

    def getHttpHost(self) -> str:
        return self._get('system', 'http_host', self._httpHost)

    def setHttpHost(self, host: str) -> None:
        self._set('system', 'http_host', host)

    def getHttpPort(self) -> int:
        return self._get('system', 'http_port', self._httpPort)

    def setHttpPort(self, port: int) -> None:
        self._set('system', 'http_port', port)

    def getCpuWarnTempC(self) -> int:
        return self._get('system', 'cpu_warn_temp_c', self._cpuWarnTempC)

    def setCpuWarnTempC(self, temp: int) -> None:
        self._set('system', 'cpu_warn_temp_c', temp)

    def getLogLevel(self) -> int:
        return self._get('system', 'log_level', self._logLevel)

    def setLogLevel(self, level: int) -> None:
        self._set('system', 'log_level', level)
        self._logger.setLevel(level)

    def getMaxSaunaOnTimeHrs(self) -> int:
        return self._get('system', 'max_sauna_on_time_hrs', self._maxSaunaOnTimeHrs)

    def setMaxSaunaOnTimeHrs(self, time: int) -> None:
        self._set('system', 'max_sauna_on_time_hrs', time)
        self._saunaOnTimer.setTimeInterval(round(self.getMaxSaunaOnTimeHrs() * 60 * 60))

    def getWebPassword(self) -> str:
        return self._get('system', 'web_password', self._webPassword)

    def setWebPassword(self, password: str) -> None:
        self._set('system', 'web_password', password)

    def getSecretKey(self) -> str:
        # Generate a new secret key if it doesn't exist
        secret = self._get('system', 'secret_key', secrets.token_hex(32))
        return secret

    # ----------------------- Not persisted attributes --------------------------

    def isSaunaOn(self) -> bool:
        return self._isSaunaOn

    def isSaunaOff(self) -> bool:
        return not self._isSaunaOn

    def turnSaunaOn(self) -> None:
        self.turnSaunaOnOff(True)

    def turnSaunaOff(self) -> None:
        self.turnSaunaOnOff(False)

    def turnSaunaOnOff(self, state: bool) -> None:
        self._isSaunaOn = state
        if  self._isSaunaOn:
            self._fanAfterSaunaOffTimer.stop()
            self._saunaOnTimer.start()
        else:
            self._fanAfterSaunaOffTimer.start()

    def getSaunaOnTimer(self) -> Timer:
        return self._saunaOnTimer

    def isFanAfterSaunaOffTimerRunning(self):
        return self._fanAfterSaunaOffTimer.isRunning()

    def isHeaterOn(self) -> bool:
        return self._isHeaterOn

    def setHeaterOn(self) -> None:
        self._isHeaterOn = True

    def setHeaterOff(self) -> None:
        self._isHeaterOn = False

    def getHotRoomTempF(self) -> float:
        return self._hotRoomTempF

    def setHotRoomTempF(self, tempF: float) -> None:
        self._hotRoomTempF = tempF

    def getHotRoomHumidity(self) -> float:
        return self._hotRoomHumidity

    def setHotRoomHumidity(self, humidity: float) -> None:
        self._hotRoomHumidity = humidity

    def isHotRoomLightOn(self) -> bool:
        return self._hotRoomLightOn

    def setHotRoomLightOnOff(self, value: bool) -> None:
        self._hotRoomLightOn = value

    def getLeftFanRpm(self) -> int:
        return self._leftFanRpm

    def setLeftFanRpm(self, rpm: int) -> None:
        self._leftFanRpm = rpm

    def getRightFanRpm(self) -> int:
        return self._rightFanRpm

    def setRightFanRpm(self, rpm: int) -> None:
        self._rightFanRpm = rpm

    def getCpuTemp(self) -> float:
        return self._cpuTempC

    def setCpuTemp(self, temp: float) -> None:
        self._cpuTempC = temp


