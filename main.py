import time
import threading
from SaunaContext import SaunaContext
from SaunaDevices import SaunaDevices
from SaunaController import SaunaController
from ErrorManager import ErrorManager
from SaunaControllerUI import SaunaControlApp

def saunaControllerLoop(ctx: SaunaContext, sd: SaunaDevices, hc: SaunaController):
    """Background thread for Sauna Control"""
    while True:
        # Heater Control
        hc.processHeater()
        # TODO verify fan status and report error. Test fan control
        time.sleep(1)

if __name__ == '__main__':
    ctx = SaunaContext()
    errorMgr = ErrorManager()

    # Initialize classes
    sd = SaunaDevices(ctx, errorMgr)
    sc = SaunaController(ctx, sd, errorMgr)
    # Start heater control loop in background thread
    saunaControllerThread = threading.Thread(target=saunaControllerLoop, args=(ctx,sd,sc,), daemon=True)
    saunaControllerThread.start()

    # Initialize Fan status
    sc.turnRightFanOnOff(ctx.getRightFanOnStatus())
    sc.turnLeftFanOnOff(ctx.getLeftFanOnStatus())

    # Run the UI application (this blocks until app closes)
    SaunaControlApp(ctx=ctx, sc=sc, sd=sd, errorMgr=errorMgr).run()







