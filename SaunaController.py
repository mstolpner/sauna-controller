import atexit
import threading
import time

from ErrorManager import ErrorManager
from HeaterController import HeaterController
from SaunaContext import SaunaContext
from SaunaDevices import SaunaDevices

# TODO add timer for max sauna on
class SaunaController:

    _ctx = None
    _errorMgr = None
    _sd = None
    _hc = None

    def __init__(self, ctx: SaunaContext, errorMgr: ErrorManager):
        self._ctx = ctx
        self._errorMgr = errorMgr
        self._sd = SaunaDevices(self._ctx, self._errorMgr)
        self._hc = HeaterController(self._ctx, self._sd, self._errorMgr)
        # Ensure safe exit
        atexit.register(self._onExit)

    def _onExit(self):
        self._ctx.turnSaunaOff()
        self._sd.turnHeaterOff()

    # ----------------------------------- Sauna Controller Run Methods ------------------------------------

    def run(self):
        # Start sauna control loop in background thread
        saunaControllerThread = threading.Thread(target=self._run, args=(), daemon=True)
        saunaControllerThread.start()

    def _run(self):
        while True:
            # Heater Control
            self._hc.process()
            # Process fans
            self._sd.turnRightFanOnOff(self._ctx.getRightFanOnStatus())
            self._sd.turnLeftFanOnOff(self._ctx.getLeftFanOnStatus())
            self._sd.setFanSpeed((self._ctx.getFanSpeedPct()))
            self._ctx.setLeftFanRpm(self._sd.getLeftFanSpeedRpm())
            self._ctx.setRightFanRpm(self._sd.getRightFanSpeedRpm())
            # Check fan health
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
            # Turn hot room light on/off
            self._sd.turnHotRoomLightOnOff(self._ctx.getHotRoomLightAlwaysOn() or self._ctx.isSaunaOn())
