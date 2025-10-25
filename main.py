import time
import threading
from SaunaContext import SaunaContext
from SaunaDevices import SaunaDevices
from HeaterController import HeaterController
from ErrorManager import ErrorManager
from SaunaControllerUI import SaunaControlApp

def saunaControllerLoop(ctx: SaunaContext, sd: SaunaDevices, hc: HeaterController):
    """Background thread for Sauna Control"""
    while True:
        # Heater Control
        hc.process()
        # Fan Control
        if ctx.getRightFanOnStatus() and sd.isRightFanOff():
            sd.turnRightFanOn()
        elif not ctx.getRightFanOnStatus() and sd.isRightFanOn():
            sd.turnRightFanOff()
        if ctx.getLeftFanOnStatus() and sd.isLeftFanOff():
            sd.turnLeftFanOn()
        elif not ctx.getLeftFanOnStatus() and sd.isLeftFanOn():
            sd.turnLeftFanOff()
        time.sleep(1)

if __name__ == '__main__':
    ctx = SaunaContext()
    errorMgr = ErrorManager()

    # Initialize classes
#    sd = SaunaDevices(ctx, errorMgr)
#    hc = HeaterController(ctx, sd, errorMgr)
    sd = None
    hc = None

    # Start heater control loop in background thread
    saunaControllerThread = threading.Thread(target=saunaControllerLoop, args=(ctx,sd,hc,), daemon=True)
    saunaControllerThread.start()

    # Run the UI application (this blocks until app closes)
    SaunaControlApp(ctx, errorMgr).run()







