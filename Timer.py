import time

from mypy.dmypy.client import is_running


class Timer:

    _startTime = 0
    _timeInterval = None
    # Active helps to return "not running" when the timer is stopped
    _active = False

    def __init__(self, timeIntervalSec: int =0):
        self._timeInterval = timeIntervalSec

    # Returns True if the timer has been started and has not exceeded preset time
    # Note if the timer has been stopped or never started, it will return False
    def isRunning(self) -> bool:
        return self._active and time.time() - self._startTime < self._timeInterval

    def setTimeInterval(self, interval):
        self._timeInterval = interval

    def restart(self) -> None:
        self.start()

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
