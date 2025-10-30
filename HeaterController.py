from SaunaContext import SaunaContext
from SaunaDevices import SaunaDevices
from ErrorManager import ErrorManager
from Timer import Timer


class HeaterController:

    # Dependencies
    _errorMgr = None
    _ctx = None
    _sd = None

    # Heater state
    _isHeaterOn = False

    # Cooling grace timer. See comments in the method below.
    _coolingGracePeriodTimer = None

    # Heater Health 
    _heaterHealthCoolDownTimer = None
    _heaterHealthWarmUpTimer = None
    _heaterMaxSafeRuntimeTimer = None
    _heaterHealthLastRefPointTemp = None

    def __init__(self, ctx: SaunaContext, sd: SaunaDevices, errorMgr: ErrorManager):
        # Initialize classes
        self._errorMgr = errorMgr
        self._ctx = ctx
        self._sd = sd
        # Initialize timers
        self._coolingGracePeriodTimer = Timer(self._ctx.getCoolingGracePeriodMin() * 60)
        self._heaterHealthCoolDownTimer = Timer(self._ctx.getHeaterHealthCooldownTimeMin() * 60)
        self._heaterHealthWarmUpTimer = Timer(self._ctx.getHeaterHealthWarmUpTimeMin() * 60)
        self._heaterMaxSafeRuntimeTimer = Timer(self._ctx.getHeaterMaxSafeRuntimeMin() * 60)
        # Initialize member variables
        self._heaterHealthLastRefPointTemp = self._sd.getHotRoomTemperature('F')

    def processHeaterControl(self) -> None:
        priorHeaterOnStatus = self._isHeaterOn
        self._isHeaterOn = self._sd.isHeaterOn()
        self._ctx.setHotRoomTempF(self._sd.getHotRoomTemperature('F'))
        self._ctx.setHotRoomHumidity(self._sd.getHotRoomHumidity())

        # Ensure the heater does not run longer than allowed max time
        if self._heaterMaxSafeRuntimeTimer.isUp():
            self._ctx.turnSaunaOff()
            self._errorMgr.raiseCriticalError(f"Heater has been continuously on for over {self._ctx.getHeaterMaxSafeRuntimeMin()} minutes.")

        # If sauna is off, ensure the heater is off.
        if self._ctx.isSaunaOff():
            if self._isHeaterOn:
                self._turnHeaterOff()

        # Allow for cooling grace period as a door might be open for a short period causing temperature to drop temporarily
        elif (not self._isHeaterOn and
              self._ctx.getHotRoomTempF() <= self._ctx.getHotRoomTargetTempF() - self._ctx.getLowerHotRoomTempThresholdF()
              and self._coolingGracePeriodTimer.isRunning()):
            # If sauna is On, do not wait grace cooling period
            if self._ctx.isSaunaOn():
                self._coolingGracePeriodTimer.stop()

        # Turn Heater Off if needed
        elif (self._isHeaterOn and
              self._ctx.getHotRoomTempF() >= self._ctx.getHotRoomTargetTempF() + self._ctx.getUpperHotRoomTempThresholdF()
              and self._ctx.isSaunaOn()):
            self._turnHeaterOff()

        # Turn Heater On if needed
        elif (not self._isHeaterOn and
              self._ctx.getHotRoomTempF() <= self._ctx.getHotRoomTargetTempF() - self._ctx.getLowerHotRoomTempThresholdF()
              and self._ctx.isSaunaOn()):
            self._turnHeaterOn()

        # Ensure contactor works properly - temperature is rising as expected
        if self._isHeaterOn and self._heaterHealthWarmUpTimer.isUp():
            if self._ctx.getHotRoomTempF() <= self._heaterHealthLastRefPointTemp:
                self._errorMgr.raiseHeaterError('Hot room temperature is not rising.')
            else:
                # All good, restart the cycle
                self._heaterHealthLastRefPointTemp = self._ctx.getHotRoomTempF()
            self._heaterHealthWarmUpTimer.start()
        # Ensure contactor works properly - temperature is falling as expected
        if not self._isHeaterOn and \
           self._ctx.getHotRoomTempF() >= self._ctx.getHotRoomTargetTempF() - self._ctx.getLowerHotRoomTempThresholdF() and \
           self._heaterHealthCoolDownTimer.isUp():
            if self._ctx.getHotRoomTempF() >= self._heaterHealthLastRefPointTemp:
                self._errorMgr.raiseHeaterError('Hot room temperature is not falling.')
            else:
                # All good, restart the cycle
                self._heaterHealthLastRefPointTemp = self._ctx.getHotRoomTempF()
            self._heaterHealthCoolDownTimer.start()

    def _turnHeaterOff(self):
        self._sd.turnHeaterOff()
        self._isHeaterOn = False
        self._heaterHealthLastRefPointTemp = self._ctx.getHotRoomTempF()
        # Set up heater health timers
        self._heaterHealthWarmUpTimer.stop()
        self._heaterHealthCoolDownTimer.start()
        self._heaterMaxSafeRuntimeTimer.start()

    def _turnHeaterOn(self):
        self._sd.turnHeaterOn()
        self._isHeaterOn = True
        self._heaterHealthLastRefPointTemp = self._ctx.getHotRoomTempF()
        # Set up heater health timers
        self._heaterHealthCoolDownTimer.stop()
        self._heaterHealthWarmUpTimer.start()
        # Set up max heater runtime timer
        self._heaterMaxSafeRuntimeTimer.start()
        # Set up grace period timer
        self._coolingGracePeriodTimer.start()
