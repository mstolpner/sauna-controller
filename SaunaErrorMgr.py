from pymodbus.exceptions import ModbusException
from SaunaContext import SaunaContext
from datetime import datetime


class SaunaErrorMgr:
    _ctx: SaunaContext
    _errors: list  # List of error dictionaries with {type, message, timestamp}

    # Error type constants
    ERROR_CRITICAL = 'critical'
    ERROR_RELAY_MODULE = 'relay_module'
    ERROR_FAN_MODULE = 'fan_module'
    ERROR_SENSOR_MODULE = 'sensor_module'
    ERROR_MODBUS = 'modbus'
    ERROR_HEATER = 'heater'
    ERROR_FAN = 'fan'
    ERROR_SYSTEM_HEALTH = 'system_health'

    def __init__(self, ctx: SaunaContext):
        self._ctx = ctx
        self._errors = []

    def _logError(self, msg: str) -> None:
        self._ctx._logger.error(msg)

    def _raiseError(self, error_type: str, message: str) -> None:
        """Add or update an error in the errors list"""
        # Check if this error type and message already exists
        existing_error = None
        for error in self._errors:
            if error['type'] == error_type and error['message'] == message:
                existing_error = error
                break

        if existing_error:
            # Update timestamp for repeated error, but don't log
            existing_error['timestamp'] = datetime.now()
        else:
            # New error - add to list and log
            self._logError(f"[{error_type}] {message}")
            self._errors.append({
                'type': error_type,
                'message': message,
                'timestamp': datetime.now()
            })

    def _eraseError(self, error_type: str) -> None:
        """Remove all errors of a specific type"""
        self._errors = [error for error in self._errors if error['type'] != error_type]

    def _getErrorMessage(self, error_type: str) -> str:
        """Get the message for a specific error type (for backward compatibility)"""
        for error in self._errors:
            if error['type'] == error_type:
                return error['message']
        return None

    def raiseCriticalError(self, errorMessage: str) -> None:
        self._raiseError(self.ERROR_CRITICAL, errorMessage)

    def eraseCriticalError(self) -> None:
        self._eraseError(self.ERROR_CRITICAL)

    @property
    def _criticalErrorMessage(self):
        """Backward compatibility property"""
        return self._getErrorMessage(self.ERROR_CRITICAL)

    def raiseRelayModuleError(self, errorMessage: str) -> None:
        self._raiseError(self.ERROR_RELAY_MODULE, errorMessage)

    def eraseRelayModuleError(self) -> None:
        self._eraseError(self.ERROR_RELAY_MODULE)

    @property
    def _relayModuleErrorMessage(self):
        """Backward compatibility property"""
        return self._getErrorMessage(self.ERROR_RELAY_MODULE)

    def raiseFanModuleError(self, errorMessage: str) -> None:
        self._raiseError(self.ERROR_FAN_MODULE, errorMessage)

    def eraseFanModuleError(self) -> None:
        self._eraseError(self.ERROR_FAN_MODULE)

    @property
    def _fanModuleErrorMessage(self):
        """Backward compatibility property"""
        return self._getErrorMessage(self.ERROR_FAN_MODULE)

    def raiseSensorModuleError(self, errorMessage: str) -> None:
        self._raiseError(self.ERROR_SENSOR_MODULE, errorMessage)

    def eraseSensorModuleError(self) -> None:
        self._eraseError(self.ERROR_SENSOR_MODULE)

    @property
    def _sensorModuleErrorMessage(self):
        """Backward compatibility property"""
        return self._getErrorMessage(self.ERROR_SENSOR_MODULE)

    def raiseModbusError(self, exception: ModbusException) -> None:
        self._raiseError(self.ERROR_MODBUS, str(exception))

    def eraseModbusError(self) -> None:
        self._eraseError(self.ERROR_MODBUS)

    @property
    def _modbusException(self):
        """Backward compatibility property"""
        return self._getErrorMessage(self.ERROR_MODBUS)

    def raiseHeaterError(self, errorMessage: str) -> None:
        self._raiseError(self.ERROR_HEATER, errorMessage)

    def eraseHeaterError(self) -> None:
        self._eraseError(self.ERROR_HEATER)

    @property
    def _heaterErrorMessage(self):
        """Backward compatibility property"""
        return self._getErrorMessage(self.ERROR_HEATER)

    def raiseFanError(self, errorMessage: str) -> None:
        self._raiseError(self.ERROR_FAN, errorMessage)

    def eraseFanError(self) -> None:
        self._eraseError(self.ERROR_FAN)

    @property
    def _fanErrorMessage(self):
        """Backward compatibility property"""
        return self._getErrorMessage(self.ERROR_FAN)

    def raiseSystemHealthError(self, errorMessage: str) -> None:
        self._raiseError(self.ERROR_SYSTEM_HEALTH, errorMessage)

    def eraseSystemHealthError(self) -> None:
        self._eraseError(self.ERROR_SYSTEM_HEALTH)

    @property
    def _systemHealthErrorMessage(self):
        """Backward compatibility property"""
        return self._getErrorMessage(self.ERROR_SYSTEM_HEALTH)

    def hasAnyError(self) -> bool:
        """Check if there are any active errors"""
        return len(self._errors) > 0

    def getAllErrors(self) -> list:
        """Get all errors with their timestamps"""
        return self._errors.copy()

    def clearAllErrors(self) -> None:
        """Clear all errors"""
        self._errors = []
