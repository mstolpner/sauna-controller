import time


class Timer:

    _startTime = 0
    _timeInterval = None
    _active = False

    def __init__(self, timeIntervalSec: int =0):
        self._timeInterval = timeIntervalSec

    def isCompleted(self) -> bool:
        if self._active and time.time() - self._startTime >= self._timeInterval:
            return True
        return False

    def isRunning(self) -> bool:
        return self._active and time.time() - self._startTime <= self._timeInterval

    def setTimeInterval(self, interval):
        self._timeInterval = interval

    def restart(self, timeInterval: int) -> None:
        self._startTime = time.time()
        self._timeInterval = timeInterval
        self._active = True

    def start(self) -> None:
        self._startTime = time.time()
        self._active = True
    
    def stop(self) -> None:
        self._startTime = 0
        self._active = False
