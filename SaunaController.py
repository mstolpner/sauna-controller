import atexit
import threading
import re, subprocess
from datetime import datetime

from SaunaErrorMgr import SaunaErrorMgr
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
                self._processSystemHealth()

    # ----------------------- Fan Control Methods --------------------------

    def _processFanControl(self):
        # Check fan health only when fan(s) are supposed to be running
        if self._sd.isLeftFanOn() or self._sd.isRightFanOn():
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
        self._sd.setFanSpeed((self._ctx.getFanSpeedPct()))
        self._ctx.setLeftFanRpm(self._sd.getLeftFanSpeedRpm())
        self._ctx.setRightFanRpm(self._sd.getRightFanSpeedRpm())

    # ----------------------- Room Light Control Methods ---------------------

    def _processHotRoomLight(self):
        # Turn hot room light on/off
        self._sd.turnHotRoomLightOnOff(self._ctx.getHotRoomLightAlwaysOn() or self._ctx.isSaunaOn())
        self._ctx.setHotRoomLightOnOff(self._ctx.getHotRoomLightAlwaysOn() or self._ctx.isSaunaOn())


    # ------------------------ Heater Control Methods ---------------------------

    # Heater may heat up faster than the heat exchange with the air. Use cyclic power heater on and off to avoid heater overheating.
    # When hot room air temperature starts falling, it maybe due to an open door for a short time. Use grace timer to avoid unnecessary heater on cycle.
    # Check heater health with
    #   1) temperature falls when the heater is off,
    #   2) temperature raises when the heater is on,
    #   3) proper current flows through the heater when the heater is on if a current sensor is present, - TODO
    #   4) heater only runs for max period of time,
    #   5) sauna is on only for certain max period of time.
    def _processHeaterControl(self) -> None:

        # Detect temp change, self._ctx.getHotRoomTempF() still has the prior iteration temp at this point
        tempFalling = self._ctx.getHotRoomTempF() > self._ctx.getHotRoomTempF()
        tempRising = self._ctx.getHotRoomTempF() < self._ctx.getHotRoomTempF()
        tempAboveTarget = self._ctx.getHotRoomTempF() >= self._ctx.getHotRoomTargetTempF() - self._ctx.getLowerHotRoomTempThresholdF()
        tempBelowTarget = self._ctx.getHotRoomTempF() <= self._ctx.getHotRoomTargetTempF() - self._ctx.getLowerHotRoomTempThresholdF()

        # Detect heater staus change
        heaterTurnedOff = self._isHeaterOn and not self._sd.isHeaterOn()
        heaterTurnedOn = not self._isHeaterOn and self._sd.isHeaterOn()
        self._isHeaterOn = self._sd.isHeaterOn()

        # Update current temp and humidity in the context for display etc.
        self._ctx.setHotRoomTempF(self._sd.getHotRoomTemperature('F'))
        self._ctx.setHotRoomHumidity(self._sd.getHotRoomHumidity())

        # Ensure the heater does not run longer than allowed max time
        if self._heaterMaxSafeRuntimeTimer.isCompleted():
            self._ctx.turnSaunaOff()
            self._errorMgr.raiseCriticalError(f"Heater has been continuously on for over {self._ctx.getHeaterMaxSafeRuntimeMin()} minutes.")

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
        if self._isHeaterOn and not self._heaterHealthWarmUpTimer.isRunning():
            if not tempRising:
                self._errorMgr.raiseHeaterError('Hot room temperature is not rising.')
            else:
                # All good, restart the cycle
                self._heaterHealthLastRefPointTemp = self._ctx.getHotRoomTempF()
            self._heaterHealthWarmUpTimer.start()

        # Ensure contactor works properly - temperature is falling as expected
        if not self._isHeaterOn and tempAboveTarget and not self._heaterHealthCoolDownTimer.isRunning():
            if not tempFalling:
                self._errorMgr.raiseHeaterError('Hot room temperature is not falling.')
            else:
                # All good, restart the cycle
                self._heaterHealthLastRefPointTemp = self._ctx.getHotRoomTempF()
            self._heaterHealthCoolDownTimer.start()

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

    # ---------------------------- System Health ---------------------------

    def _processSystemHealth(self):
        err, msg = subprocess.getstatusoutput('vcgencmd measure_temp')
        if not err:
            m = re.search(r'-?\d\.?\d*', msg)
            try:
                self._ctx.setCpuTemp(float(m.group()))
                if self._ctx.getCpuTemp() > self._ctx.getCpuWarnTempC():
                    self._errorMgr.raiseSystemHealthError(f"CPU Temperature is {self._ctx.getCpuTemp()}°C")
                else:
                    self._errorMgr.eraseSystemHealthError()
            except ValueError:  # catch only error needed
                pass