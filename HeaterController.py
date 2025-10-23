import time
from SaunaContext import SaunaContext
from SaunaDevices import SaunaDevices
from Timer import Timer
from ErrorManager import ErrorManager


class HeaterController:

    # Hot room temperature manipulation
    _hotRoomTempF = 0
    _isHeaterOn = False

    # Errors Manager
    _errorMgr = None

    # Heating/cooling grace timers
    _coolingGracePeriodTimer = None

    # Heater Health 
    _heaterHealthCoolDownTimer = None
    _heaterHealthWarmUpTimer = None
    _heaterHealthLastRefPointTemp = None

    _ctx = None
    _devices = None

    _lastTimeHotRoomTempDroppedBelowTarget = time.time()
    _lastIterationHotRoomTemperatureBelowTarget = True

    def __init__(self, ctx: SaunaContext, devices: SaunaDevices):
        # Initialize classes
        self._errorMgr = ErrorManager()
        self._ctx = ctx
        self._devices = devices
        # Initialize timers
        self._coolingGracePeriodTimer = Timer(self._ctx.getCoolingGracePeriod())
        self._heaterHealthCoolDownTimer = Timer(self._ctx.getHeaterHealthCooldownTime())
        self._heaterHealthWarmUpTimer = Timer(self._ctx.getHeaterHealthWarmUpTime())
        self._heaterHealthLastRefPointTemp = self._devices.getHotRoomTemperature('F')
        self._ctx.turnSaunaOn()

    def process(self) -> None:
        priorHeaterOnStatus = self._isHeaterOn
        self._isHeaterOn = self._devices.isHeaterOn()

        # If sauna is off, ensure the heater is off and the hot room is cooling down. TODO
        if self._ctx.isSaunaOff():
            if self._isHeaterOn:
                self._devices.turnHeaterOff()
            return
        
        self._hotRoomTempF = self._devices.getHotRoomTemperature('F')

        # Allow for cooling grace period as a door might be open for a short period causing temperature to drop temporarily
        if not self._isHeaterOn and self._hotRoomTempF <= self._ctx.getHotRoomTargetTempF() - self._ctx.getLowerHotRoomTempThreasholdF() \
           and self._coolingGracePeriodTimer.isActive():
            # Wait for the grace cooling timer
            pass
        # Turn Heater Off if needed
        elif self._isHeaterOn and self._hotRoomTempF >= self._ctx.getHotRoomTargetTempF() + self._ctx.getUpperHotRoomTempThreasholdF():
            self._devices.turnHeaterOff()
            self._isHeaterOn = False
            self._heaterHealthLastRefPointTemp = self._hotRoomTempF
            # Set up heater health timers
            self._heaterHealthWarmUpTimer.stop()
            self._heaterHealthCoolDownTimer.start()
        # Turn Heater On if needed
        elif not self._isHeaterOn and self._hotRoomTempF <= self._ctx.getHotRoomTargetTempF() - self._ctx.getLowerHotRoomTempThreasholdF():
            self._devices.turnHeaterOn()
            self._isHeaterOn = True
            self._heaterHealthLastRefPointTemp = self._hotRoomTempF
            # Set up heater health timers
            self._heaterHealthCoolDownTimer.stop()
            self._heaterHealthWarmUpTimer.start()
            # Set up grace period timer
            self._coolingGracePeriodTimer.start()

        # Ensure contactor works properly - temperature is rising or falling as expected
        if self._isHeaterOn and self._heaterHealthWarmUpTimer.isFinished():
            if self._hotRoomTempF <= self._heaterHealthLastRefPointTemp:
                self._errorMgr.raiseHeaterError('Hot room tempreture is not rising.')
            else:
                # All good, restart the cycle
                self._heaterHealthLastRefPointTemp = self._hotRoomTempF
            self._heaterHealthWarmUpTimer.start()
        if not self._isHeaterOn and self._heaterHealthCoolDownTimer.isFinished():
            if self._hotRoomTempF >= self._heaterHealthLastRefPointTemp:
                self._errorMgr.raiseHeaterError('Hot room tempreture is not falling.')
            else:
                # All good, restart the cycle
                self._heaterHealthLastRefPointTemp = self._hotRoomTempF
            self._heaterHealthCoolDownTimer.start()
