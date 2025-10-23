import time


class Timer:

    _startTime = 0
    _timeInterval = None

    def __init__(self, timeInterval: int =0):
        self._timeInterval = timeInterval

    def isFinished(self) -> bool:
        if self._startTime == 0:
            return True
        if time.time() - self._startTime >= self._timeInterval:
            self._startTime = 0
            return True
        return False

    def isActive(self) -> bool:
        return not self.isFinished()

    def setTimeInterval(self, interval):
        self._timeInterval = interval

    def restart(self) -> None:
        self.start()

    def restart(self, timeInterval: int) -> None:
        self._startTime = time.time()
        self._timeInterval = timeInterval

    def start(self) -> None:
        self._startTime = time.time()
    
    def stop(self) -> None:
        self._startTime = 0
