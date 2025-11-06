from pymodbus.exceptions import ModbusException
from SaunaContext import SaunaContext


class SaunaErrorMgr:
    _ctx: SaunaContext
    _criticalErrorMessage = None
    _relayModuleErrorMessage = None
    _fanModuleErrorMessage = None
    _sensorModuleErrorMessage = None
    _modbusException = None
    _heaterErrorMessage = None
    _fanErrorMessage = None
    _systemHealthErrorMessage = None

    def __init__(self, ctx: SaunaContext):
        self._ctx = ctx

    def _logError(self, msg: str) -> None:
        self._ctx._logger.error(msg)

    def raiseCriticalError(self, errorMessage: str) -> None:
        self._logError(errorMessage)
        self._criticalErrorMessage = errorMessage

    def eraseCriticalError(self) -> None:
        self._criticalErrorMessage = None

    def raiseRelayModuleError(self, errorMessage: str) -> None:
        self._logError(errorMessage)
        self._relayModuleErrorMessage = errorMessage

    def eraseRelayModuleError(self) -> None:
        self._relayModuleErrorMessage = None

    def raiseFanModuleError(self, errorMessage: str) -> None:
        self._logError(errorMessage)
        self._fanModuleErrorMessage = errorMessage

    def eraseFanModuleError(self) -> None:
        self._fanModuleErrorMessage = None

    def raiseSensorModuleError(self, errorMessage: str) -> None:
        self._logError(errorMessage)
        self._sensorModuleErrorMessage = errorMessage

    def eraseSensorModuleError(self) -> None:
        self._sensorModuleErrorMessage = None

    def raiseModbusError(self, exception: ModbusException) -> None:
        self._logError(exception)
        self._modbusException = exception

    def eraseModbusError(self) -> None:
        self._modbusException = None

    def raiseHeaterError(self, errorMessage: str) -> None:
        self._logError(errorMessage)
        self._heaterErrorMessage = errorMessage

    def eraseHeaterError(self) -> None:
        self._heaterErrorMessage = None

    def raiseFanError(self, errorMessage: str) -> None:
        self._logError(errorMessage)
        self._fanErrorMessage = errorMessage

    def eraseFanError(self) -> None:
        self._fanErrorMessage = None

    def raiseSystemHealthError(self, errorMessage: str) -> None:
        self._logError(errorMessage)
        self._systemHealthErrorMessage = errorMessage

    def eraseSystemHealthError(self) -> None:
        self._systemHealthErrorMessage = None

    def hasAnyError(self) -> bool:
        """Check if there are any active errors"""
        return any([
            self._criticalErrorMessage,
            self._relayModuleErrorMessage,
            self._fanModuleErrorMessage,
            self._sensorModuleErrorMessage,
            self._modbusException,
            self._heaterErrorMessage,
            self._fanErrorMessage,
            self._systemHealthErrorMessage
        ])

    def clearAllErrors(self) -> None:
        """Clear all errors"""
        self.eraseCriticalError()
        self.eraseRelayModuleError()
        self.eraseFanModuleError()
        self.eraseSensorModuleError()
        self.eraseModbusError()
        self.eraseHeaterError()
        self.eraseFanError()
        self.eraseSystemHealthError()
