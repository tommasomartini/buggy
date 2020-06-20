import logging

from gpiozero import LED

_logger = logging.getLogger(__name__)

PIN = 23


class Status:
    AUTOPILOT = 0
    READING_REMOTE = 1
    WAITING_FOR_REMOTE = 2


_blinking_time_s = {
    Status.AUTOPILOT: 0.5,
    Status.READING_REMOTE: -1,
    Status.WAITING_FOR_REMOTE: 0.05,
}


class StatusLed:

    def __init__(self):
        self._led = LED(PIN)
        self._led.off()

    def set(self, status):
        self._led.off()
        blinking_time_s = _blinking_time_s.get(status)
        if blinking_time_s is None:
            raise ValueError('Unknown status: {}'.format(status))

        if blinking_time_s < 0:
            # Constant on.
            self._led.on()

        else:
            self._led.blink(on_time=blinking_time_s)

    def close(self):
        self._led.off()
        self._led.close()
