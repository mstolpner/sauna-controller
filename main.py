import time
from SaunaContext import SaunaContext
from SaunaDevices import SaunaDevices
from HeaterController import HeaterController


if __name__ == '__main__':

    # Initialize classes
    ctx = SaunaContext()
    sd = SaunaDevices(ctx)
    hc = HeaterController(ctx, sd)

    h = sd.getHotRoomHumidity()
    t = sd.getHotRoomTemperature()
    c = sd.getHotRoomTemperature('C')
    hs = sd.isHeaterOff()
    lf = sd.isLeftFanOn()
    rf = sd.isRightFanOn()
    sd.turnRightFanOn()
    rf = sd.isRightFanOn()
    sd.turnLeftFanOn()
    lf = sd.isLeftFanOn()
    sl = sd.isLeftFanOk()
    sr = sd.isRightFanOk()


    # Main Application Loop
    while True:

        hc.process()
        time.sleep(1)







