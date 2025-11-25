import atexit
import threading
import re, subprocess

from core.HeaterController import HeaterController
from core.SaunaErrorMgr import SaunaErrorMgr
from core.SaunaContext import SaunaContext
from hardware.SaunaDevices import SaunaDevices


class SaunaController:

    _ctx : SaunaContext = None
    _errorMgr : SaunaErrorMgr = None
    _sd : SaunaDevices = None
    _hc : HeaterController = None

    # Is the app in the exiting process
    _isOnExit = False

    def __init__(self, ctx: SaunaContext, errorMgr: SaunaErrorMgr):
        # Initialize dependencies/classes
        self._ctx = ctx
        self._errorMgr = errorMgr
        self._sd = SaunaDevices(self._ctx, self._errorMgr)
        self._hc = HeaterController(self._sd, self._ctx, self._errorMgr)
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
                self._hc.processHeaterControl()
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