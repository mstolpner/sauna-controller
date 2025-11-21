import atexit
import threading
import re, subprocess
from datetime import datetime

from SaunaErrorMgr import SaunaErrorMgr
from SaunaContext import SaunaContext
from SaunaDevices import SaunaDevices
from Timer import Timer


class HeaterController:

    _ctx : SaunaContext = None
    _errorMgr : SaunaErrorMgr = None
    _sd : SaunaDevices = None

    # Heater state
    _isHeaterOn = False

    # Cooling grace timer. See comments in the method below.
    _coolingGracePeriodTimer = None

    # Heater Health
    _heaterHealthCoolDownTimer = None
    _heaterHealthWarmUpTimer = None
    _heaterMaxSafeRuntimeTimer = None
    _heaterHealthLastRefPointTemp = None
    # Heater timers
    _heaterOnCycleTimer = Timer()
    _heaterOffCycleTimer = Timer()


    def __init__(self, ctx: SaunaContext, errorMgr: SaunaErrorMgr):
        # Initialize dependencies/classes
        self._ctx = ctx
        self._errorMgr = errorMgr
        self._sd = SaunaDevices(self._ctx, self._errorMgr)
        # Initialize timers
        self._coolingGracePeriodTimer = Timer(self._ctx.getCoolingGracePeriodMin() * 60)
        self._heaterHealthCoolDownTimer = Timer(self._ctx.getHeaterHealthCooldownTimeMin() * 60)
        self._heaterHealthWarmUpTimer = Timer(self._ctx.getHeaterHealthWarmUpTimeMin() * 60)
        self._heaterMaxSafeRuntimeTimer = Timer(self._ctx.getHeaterMaxSafeRuntimeMin() * 60)
        # Initialize member variables
        self._heaterHealthLastRefPointTemp = self._sd.getHotRoomTemperature('F')

    # Heater may heat up faster than the heat exchange with the air. Use cyclic power heater on and off to avoid heater overheating.
    # When hot room air temperature starts falling, it maybe due to an open door for a short time. Use grace timer to avoid unnecessary heater on cycle.
    # Check heater health with
    #   1) temperature falls when the heater is off,
    #   2) temperature raises when the heater is on,
    #   3) proper current flows through the heater when the heater is on if a current sensor is present, - TODO
    #   4) heater only runs for max period of time,
    #   5) sauna is on only for certain max period of time.
    def processHeaterControl(self) -> None:

        # Detect temp change, self._ctx.getHotRoomTempF() still has the prior iteration temp at this point.
        # Get the current hot room temp first to avoid racing conditions
        currentHotRoomTemp = self._sd.getHotRoomTemperature('F')
        tempFalling = self._ctx.getHotRoomTempF() > currentHotRoomTemp
        tempRising = self._ctx.getHotRoomTempF() < currentHotRoomTemp
        tempAboveTarget = currentHotRoomTemp >= self._ctx.getHotRoomTargetTempF() - self._ctx.getLowerHotRoomTempThresholdF()
        tempBelowTarget = currentHotRoomTemp <= self._ctx.getHotRoomTargetTempF() - self._ctx.getLowerHotRoomTempThresholdF()

        # Update current temp and humidity in the context for display etc.
        self._ctx.setHotRoomTempF(currentHotRoomTemp)
        self._ctx.setHotRoomHumidity(self._sd.getHotRoomHumidity())

        # Detect heater staus change
        heaterTurnedOff = self._isHeaterOn and not self._sd.isHeaterOn()
        heaterTurnedOn = not self._isHeaterOn and self._sd.isHeaterOn()
        self._isHeaterOn = self._sd.isHeaterOn()

        # Ensure the heater does not run longer than allowed max time
#        if not self._heaterMaxSafeRuntimeTimer.isRunning():
#            self._ctx.turnSaunaOff()
#            self._errorMgr.raiseCriticalError(f"Heater has been continuously on for over {self._ctx.getHeaterMaxSafeRuntimeMin()} minutes.")

        # If sauna is off, ensure the heater is off.
        if self._ctx.isSaunaOff():
            self._turnHeaterOff()
        # Make sure sauna is not on longer than configured
        elif self._ctx.isSaunaOn() and not self._ctx.getSaunaOnTimer().isRunning():
            self._ctx.turnSaunaOff()
        # If temperature is falling while the heater is off, start cooling grace period timer
        # as a door might be open for a short period of time causing temperature to drop temporarily.
        elif (not self._isHeaterOn
              and tempFalling
              and not self._coolingGracePeriodTimer.isRunning()):
                self._coolingGracePeriodTimer.start()
        # Turn Heater Off for heater cycling if On cycle is finished
        elif (self._isHeaterOn
              # Wait for the "on" heater cycle
              and not self._heaterOnCycleTimer.isRunning()):
            self._turnHeaterOff()
        # Turn Heater Off if temperature reached
        elif self._isHeaterOn and tempAboveTarget:
            self._turnHeaterOff()
        # Turn Heater On for heater cycling or if temperature is below target
        elif (not self._isHeaterOn and tempBelowTarget
              # Allow for cooling grace period as a door might be open for a short period causing temperature to drop temporarily
              and not self._coolingGracePeriodTimer.isRunning()
              # Wait for the "off" heater cycle
              and not self._heaterOffCycleTimer.isRunning()
              # Make sure Sauna is ON
              and self._ctx.isSaunaOn()):
            self._turnHeaterOn()

        # Ensure contactor and heater work properly - temperature is rising as expected
        if self._isHeaterOn and not self._heaterHealthWarmUpTimer.isRunning() and not tempRising:
            self._errorMgr.raiseHeaterError('Hot room temperature is not rising.')
        if self._isHeaterOn and tempRising:
            self._heaterHealthWarmUpTimer.start()
            self._errorMgr.eraseHeaterError()

        # Ensure contactor works properly - temperature is falling as expected
        if not self._isHeaterOn and not self._heaterHealthCoolDownTimer.isRunning() and not tempFalling:
            self._errorMgr.raiseHeaterError('Hot room temperature is not falling.')
        if not self._isHeaterOn and tempFalling:
            self._heaterHealthCoolDownTimer.start()
            self._errorMgr.eraseHeaterError()

    def _turnHeaterOff(self):
        if self._isHeaterOn:
            self._ctx.getLogger().info(f'{datetime.now()} turn heat off')
        self._sd.turnHeaterOff()
        self._isHeaterOn = False
        self._heaterHealthLastRefPointTemp = self._ctx.getHotRoomTempF()
        # Set up heater health timers
        self._heaterHealthWarmUpTimer.stop()
        self._heaterHealthCoolDownTimer.start()
        self._heaterMaxSafeRuntimeTimer.stop()
        # Set Heater On Cycle Timer only if the sauna is ON
        if self._ctx.isSaunaOn():
            self._heaterOffCycleTimer.restart(self._ctx.getHeaterCycleOffPeriodMin() * 60)
        else:
            self._heaterOffCycleTimer.stop()
        self._heaterOnCycleTimer.stop()
        # Stop heater cooling grace period as it's only needed when the heater is on
        self._coolingGracePeriodTimer.stop()

    def _turnHeaterOn(self):
        if not self._ctx.isSaunaOn():
            self._errorMgr.raiseCriticalError('Attempt to turn Heater On while Sauna is OFF.')
            return
        if not self._isHeaterOn:
            self._ctx.getLogger().info(f'{datetime.now()} turn heat on')
        # Set up heater safety timers
        self._heaterHealthWarmUpTimer.start()
        self._heaterMaxSafeRuntimeTimer.start()
        self._sd.turnHeaterOn()
        self._isHeaterOn = True
        self._heaterHealthLastRefPointTemp = self._ctx.getHotRoomTempF()
        # Set up heater safety timers
        self._heaterHealthCoolDownTimer.stop()
        # Set Heater Cycle Timers
        self._heaterOnCycleTimer.restart(self._ctx.getHeaterCycleOnPeriodMin() * 60)
        self._heaterOffCycleTimer.stop()
