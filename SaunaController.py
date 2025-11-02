import atexit
import threading

from ErrorManager import ErrorManager
from SaunaContext import SaunaContext
from SaunaDevices import SaunaDevices
from Timer import Timer


class SaunaController:

    _ctx = None
    _errorMgr = None
    _sd = None

    # Heater state
    _isHeaterOn = False

    # Is the app in the exiting process
    _isOnExit = False

    # Cooling grace timer. See comments in the method below.
    _coolingGracePeriodTimer = None

    # Heater Health
    _heaterHealthCoolDownTimer = None
    _heaterHealthWarmUpTimer = None
    _heaterMaxSafeRuntimeTimer = None
    _heaterHealthLastRefPointTemp = None


    def __init__(self, ctx: SaunaContext, errorMgr: ErrorManager):
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
        # Ensure safe exit
        atexit.register(self._onExit)

    def _onExit(self):
        self._isOnExit = True
        self._ctx.turnSaunaOff()

    # ----------------------------------- Sauna Controller Run Methods ------------------------------------

    def run(self):
        # Start sauna control loop in background thread
        saunaControllerThread = threading.Thread(target=self._run, args=(), daemon=True)
        saunaControllerThread.start()

    def _run(self):
        while True:
            if self._isOnExit:
                self._sd.turnHeaterOff()
                self._sd.turnLeftFanOff()
                self._sd.turnRightFanOff()
            else:
                self._processHeaterControl()
                self._processFanControl()
                self._processHotRoomLight()

    # ----------------------- Fan Control Methods --------------------------

    def _processFanControl(self):
        # Check fan health only when fan(s) are supposed to be running
        if self._sd.isLeftFanOn() or self._sd.isRightFanOn():
#        if (((self._ctx.isRightFanEnabled() or self._ctx.isLeftFanEnabled()) and self._ctx._isSaunaOn) or
#                self._ctx.isFanAfterSaunaOffTimerRunning()):
            leftFanOk = self._sd.isLeftFanOk()
            rightFanOk = self._sd.isRightFanOk()
            errMsg = ''
            if not leftFanOk:
                errMsg += " Left fan does not work properly."
            if not rightFanOk:
                errMsg += " Right fan does not work properly."
            if rightFanOk and leftFanOk:
                self._errorMgr.eraseFanError()
            else:
                self._errorMgr.raiseFanError(errMsg)
        else:
            self._errorMgr.eraseFanError()
        # Process SaunaOFF situation with a delayed fan turn off
        if self._sd.isRightFanOn() \
            and (not self._ctx.isRightFanEnabled() or (not self._ctx.isSaunaOn()
                 and not self._ctx.isFanAfterSaunaOffTimerRunning())):
            self._sd.turnRightFanOff()
        elif self._sd.isRightFanOff() \
            and (self._ctx.isRightFanEnabled() and (self._ctx.isSaunaOn() or self._ctx.isFanAfterSaunaOffTimerRunning())):
            self._sd.turnRightFanOn()
        if self._sd.isLeftFanOn() \
            and (not self._ctx.isLeftFanEnabled() or (not self._ctx.isSaunaOn()
                 and not self._ctx.isFanAfterSaunaOffTimerRunning())):
            self._sd.turnLeftFanOff()
        elif self._sd.isLeftFanOff() \
            and (self._ctx.isLeftFanEnabled() and (self._ctx.isSaunaOn() or self._ctx.isFanAfterSaunaOffTimerRunning())):
            self._sd.turnLeftFanOn()

#        self._sd.turnRightFanOnOff(self._ctx.isRightFanEnabled() and (self._ctx._isSaunaOn() or
#                                                                      self._ctx.isFanAfterSaunaOffTimerRunning()))
#        self._sd.turnLeftFanOnOff(self._ctx.isLeftFanEnabled() and (self._ctx._isSaunaOn() or
#                                                                    self._ctx.isFanAfterSaunaOffTimerRunning()))
        self._sd.setFanSpeed((self._ctx.getFanSpeedPct()))
        self._ctx.setLeftFanRpm(self._sd.getLeftFanSpeedRpm())
        self._ctx.setRightFanRpm(self._sd.getRightFanSpeedRpm())

    # ----------------------- Room Light Control Methods ---------------------

    def _processHotRoomLight(self):
        # Turn hot room light on/off
        self._sd.turnHotRoomLightOnOff(self._ctx.getHotRoomLightAlwaysOn() or self._ctx.isSaunaOn())
        self._ctx.setHotRoomLightOnOff(self._ctx.getHotRoomLightAlwaysOn() or self._ctx.isSaunaOn())


    # ------------------------ Heater Control Methods ---------------------------

    def _processHeaterControl(self) -> None:
        priorHeaterOnStatus = self._isHeaterOn
        self._isHeaterOn = self._sd.isHeaterOn()
        self._ctx.setHotRoomTempF(self._sd.getHotRoomTemperature('F'))
        self._ctx.setHotRoomHumidity(self._sd.getHotRoomHumidity())

        # Ensure the heater does not run longer than allowed max time
        if self._heaterMaxSafeRuntimeTimer.isCompleted():
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
        if self._isHeaterOn and self._heaterHealthWarmUpTimer.isCompleted():
            if self._ctx.getHotRoomTempF() <= self._heaterHealthLastRefPointTemp:
                self._errorMgr.raiseHeaterError('Hot room temperature is not rising.')
            else:
                # All good, restart the cycle
                self._heaterHealthLastRefPointTemp = self._ctx.getHotRoomTempF()
            self._heaterHealthWarmUpTimer.start()
        # Ensure contactor works properly - temperature is falling as expected
        if not self._isHeaterOn and \
           self._ctx.getHotRoomTempF() >= self._ctx.getHotRoomTargetTempF() - self._ctx.getLowerHotRoomTempThresholdF() and \
           self._heaterHealthCoolDownTimer.isCompleted():
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
