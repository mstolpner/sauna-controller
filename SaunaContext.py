from typing import Any, Optional
from configobj import ConfigObj
import os
import subprocess

from ErrorManager import ErrorManager
from Timer import Timer


class SaunaContext:
    _errorMgr: ErrorManager = None
    # RS485 Serial Port Default Settings
    _rs485SerialPort = '/dev/ttyAMA0'
    _rs485SerialBaudRate: int = 9600
    _rs485SerialTimeout: float = 0.3
    _rs485SerialRetries: int = 3
    # Modbus Default Settings
    _saunaSensorsDeviceId: int = 1
    _relayModuleDeviceId: int = 2
    _fanControlModuleDeviceId: int = 3
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
    # Web Server Default Settings
    _httpHost = '0.0.0.0'
    _httpPort: int = 8080
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
    _cpuTemp = 0
    # Fan control timer
    _fanAfterSaunaOffTimer = None

#TODO add parameters for cycling heater, all parameters to settings scree. Split settings screen. add errors to fan settings.
    #TODO reduce icon size
    def __init__(self, errorMgr: ErrorManager):
        self._errorMgr = errorMgr
        iniFileExists = os.path.exists(self._configFileName)
        self._configObj = ConfigObj(self._configFileName)
        if not iniFileExists:
            self._errorMgr.logWarn('File sauna.ini not found. Creating a new file with default configuration.')
            self.setDefaultSettings()
            self.persist()
        # Initialize suna off timer
        self._fanAfterSaunaOffTimer = Timer(round(self.getFanRunningTimeAfterSaunaOffHrs() * 60 * 60))


    def setDefaultSettings(self):
        self._configObj['rs485'] = {}
        self._configObj['rs485']['sensors_module_device_id'] = self._saunaSensorsDeviceId
        self._configObj['rs485']['relay_module_device_id'] = self._relayModuleDeviceId
        self._configObj['rs485']['fan_module_device_id'] = self._fanControlModuleDeviceId
        self._configObj['rs485']['serial_port_name'] = self._rs485SerialPort
        self._configObj['rs485']['serial_baud_rate'] = self._rs485SerialBaudRate
        self._configObj['rs485']['serial_timeout'] = self._rs485SerialTimeout
        self._configObj['rs485']['serial_retries'] = self._rs485SerialRetries
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
        self._configObj['fan_control']['left_fan_enabled'] = self._leftFanOnStatus
        self._configObj['fan_control']['right_fan_enabled'] = self._rightFanOnStatus
        self._configObj['fan_control']['running_time_after_sauna_off_hrs'] = self._fanRunningTimeAfterSaunaOffHrs
        self._configObj['hot_room_control'] = {}
        self._configObj['hot_room_control']['hot_room_light_always_on'] = self._hotRoomLightAlwaysOn
        self._configObj['heater_control'] = {}
        self._configObj['heater_control']['heater_health_warmup_time_min'] = self._heaterHealthWarmUpTimeMin
        self._configObj['heater_control']['heater_health_cooldown_time_min'] = self._heaterHealthCoolDownTimeMin
        self._configObj['heater_control']['heater_max_safe_runtime_min'] = self._heaterMaxSafeRuntimeMin
        self._configObj['display'] = {}
        self._configObj['display']['display_width'] = self._displayWidth
        self._configObj['display']['display_height'] = self._displayHeight
        self._configObj['display']['display_rotation'] = self._displayRotation
        self._configObj['display']['display_device_path'] = self._displayDevicePath
        self._configObj['display']['display_brightness'] = self._displayBrightness
        self._configObj['webui'] = {}
        self._configObj['webui']['http_host'] = self._httpHost
        self._configObj['webui']['http_port'] = self._httpPort

    def persist(self):
        self._configObj.write()

    # ----------------------- RS485 configuration attributes --------------------------

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

    # ------------------------ RS485 Modbus Configuration -----------------------

    def getSaunaSensorsDeviceId(self) -> int:
        return self._get('rs485', 'sensors_module_device_id', self._saunaSensorsDeviceId)

    def setSaunaSensorsDeviceId(self, saunaSensorsDeviceId: int) -> None:
        self._set('rs485', 'sensors_module_device_id', saunaSensorsDeviceId)

    def getRelayModuleDeviceId(self) -> int:
        return self._get('rs485', 'relay_module_device_id', self._relayModuleDeviceId)

    def setRelayModuleDeviceId(self, relayModuleDeviceId: int) -> None:
        self._set('rs485', 'relay_module_device_id', relayModuleDeviceId)

    def getFanControlModuleDeviceId(self) -> int:
        return self._get('rs485', 'fan_module_device_id', self._fanControlModuleDeviceId)

    def setFanControlModuleDeviceId(self, fanControlModuleDeviceId: int) -> None:
        self._set('rs485', 'fan_module_device_id', fanControlModuleDeviceId)

    def getRs485SerialPort(self) -> str:
        return self._get('rs485', 'serial_port_name', self._rs485SerialPort)

    def setRs485SerialPort(self, rs485SerialPort: str) -> None:
        self._set('rs485', 'serial_port_name', rs485SerialPort)

    def getRs485SerialBaudRate(self) -> int:
        return self._get('rs485', 'serial_baud_rate', self._rs485SerialBaudRate)

    def setRs485SerialBaudRate(self, rs485SerialBaudRate: int) -> None:
        self._set('rs485', 'serial_baud_rate', rs485SerialBaudRate)

    def getRs485SerialTimeout(self) -> float:
        return self._get('rs485', 'serial_timeout', self._rs485SerialTimeout)

    def setRs485SerialTimeout(self, rs485SerialTimeout: float) -> None:
        self._set('rs485', 'serial_timeout', rs485SerialTimeout)

    def getRs485SerialRetries(self) -> int:
        return self._get('rs485', 'serial_retries', self._rs485SerialRetries)

    def setRs485SerialRetries(self, rs485SerialRetries: int) -> None:
        self._set('rs485', 'serial_retries', rs485SerialRetries)

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


    # -------------------------- Web UI --------------------------------

    def getHttpHost(self) -> str:
        return self._get('webui', 'http_host', self._httpHost)

    def setHttpHost(self, host: str) -> None:
        self._set('webui', 'http_host', host)

    def getHttpPort(self) -> int:
        return self._get('webui', 'http_port', self._httpPort)

    def setHttpPort(self, port: int) -> None:
        self._set('webui', 'http_port', port)

    # ----------------------- Not persisted attributes --------------------------

    def isSaunaOn(self) -> bool:
        return self._isSaunaOn

    def isSaunaOff(self) -> bool:
        return not self._isSaunaOn

    def turnSaunaOn(self) -> None:
        self._isSaunaOn = True
        self._fanAfterSaunaOffTimer.stop()

    def turnSaunaOff(self) -> None:
        self._isSaunaOn = False
        self._fanAfterSaunaOffTimer.start()

    def turnSaunaOnOff(self, state: bool) -> None:
        self._isSaunaOn = state
        if  self._isSaunaOn:
            self._fanAfterSaunaOffTimer.stop()
        else:
            self._fanAfterSaunaOffTimer.start()

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
        return self._cpuTemp

    def setCpuTemp(self, temp: float) -> None:
        self._cpuTemp = temp


