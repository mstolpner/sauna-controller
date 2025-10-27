import atexit
import threading
import time

from ErrorManager import ErrorManager
from HeaterController import HeaterController
from SaunaContext import SaunaContext
from SaunaDevices import SaunaDevices


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
        # Give it a chance to turn heater off
        time.sleep(10)

    # ----------------------------------- Sauna Controller Run Methods ------------------------------------

    def run(self):
        # Start sauna control loop in background thread
        saunaControllerThread = threading.Thread(target=self._run, args=(), daemon=True)
        saunaControllerThread.start()

    def _run(self):
        """Background thread for Sauna Control"""
        while True:
            # Heater Control
            self._hc.process()
            # Process fans
            self._sd.turnRightFanOnOff(self._ctx.getRightFanOnStatus())
            self._sd.turnLeftFanOnOff(self._ctx.getLeftFanOnStatus())
            self._sd.setFanSpeed((self._ctx.getFanSpeedPct()))
            # Check fan health
            if not self._sd.isLeftFanOk() or not self._sd.isRightFanOk():
                self._errorMgr.raiseFanError("One or more fans do not work properly.")
            else:
                self._errorMgr.eraseFanError()
            # Turn hot room light on/off
            self._sd.turnHotRoomLightOnOff(self._ctx.getHotRoomLightAlwaysOn() or self._ctx.isSaunaOn())


            time.sleep(0.5)