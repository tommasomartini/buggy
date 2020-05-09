import logging
import time

import RPi.GPIO as GPIO

TRIG_PIN = 17
ECHO_PIN = 27

# From documentation:
#   https://www.robotshop.com/media/files/pdf/hc-sr05-ultrasonic-range-finder-datasheet.pdf
_SENSOR_NAME = 'HC-SR05'
_PULSE_DURATION_s = 10e-6       # 10 microseconds
# It is recommended to trigger at most every 60 ms.
_MEASURE_INTERVAL_s = 60e-3

# Set to True if the ECHO pin is low by default and set to high when a pulse is
# detected; False otherwise.
_ECHO_IS_PULL_UP = True

# Constants.
_SPEED_OF_SOUND_mps = 343.26    # m/s
_INIT_SETUP_TIME_s = 0.2

# Speed-up constants: values that we precompute to save operations at runtime.

# The formula to convert the pulse duration to distance in centimeters is:
#   distance_cm = pulse_duration_s * speed_sound_mps * 100 / 2
# where the x100 is to convert meters in centimeters. The pulse duration equals
# the time from emission to reception, that is the time the sound travelled
# to the target and back. We divide by 2 to consider the distance covered
# in a one-way trip.
_PULSE_TO_DISTANCE_MULTIPLIER_cmps = _SPEED_OF_SOUND_mps * 100 / 2

# We experienced some freezing when using the nominal interval. We allow for
# some slack time.
_EFFECTIVE_MEASURE_INTERVAL_s = 1.2 * _MEASURE_INTERVAL_s


class UltrasonicSensor:

    def __init__(self, trig_pin, echo_pin, is_pull_up, name=None):
        self._trig_pin = trig_pin
        self._echo_pin = echo_pin
        self._is_pull_up = is_pull_up
        self._name = name
        self._logger_prefix = '[{}] '.format(self._name) if self._name else ''

        _logger.info('{}Initializing '
                     'ultrasonic sensor...'.format(self._logger_prefix))

        GPIO.setup(self._trig_pin, GPIO.OUT)
        GPIO.setup(self._echo_pin, GPIO.IN)
        time.sleep(_INIT_SETUP_TIME_s)

        _logger.info('{}Initialized'.format(self._logger_prefix))

    def read(self):
        while True:
            # Generate a trigger pulse.
            GPIO.output(self._trig_pin, True)
            time.sleep(_PULSE_DURATION_s)
            GPIO.output(self._trig_pin, False)

            # Record the time when the pulse is received back.
            while GPIO.input(self._echo_pin) == (not self._is_pull_up):
                pass
            pulse_start = time.time()
            while GPIO.input(self._echo_pin) == self._is_pull_up:
                pass

            pulse_duration = time.time() - pulse_start
            distance_cm = pulse_duration * _PULSE_TO_DISTANCE_MULTIPLIER_cmps

            yield distance_cm

            time.sleep(_EFFECTIVE_MEASURE_INTERVAL_s)

    def close(self):
        GPIO.cleanup((self._trig_pin, self._echo_pin))
        _logger.info('{}Shut down'.format(self._logger_prefix))


def _main():
    GPIO.setmode(GPIO.BCM)

    sensor = UltrasonicSensor(trig_pin=TRIG_PIN,
                              echo_pin=ECHO_PIN,
                              is_pull_up=_ECHO_IS_PULL_UP,
                              name=_SENSOR_NAME)

    try:
        for distance_cm in sensor.read():
            _logger.info('[{}] Distance: {:6.2f} cm'.format(_SENSOR_NAME,
                                                            distance_cm))
    except KeyboardInterrupt:
        pass

    sensor.close()
    print('Bye!')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    _logger = logging.getLogger(__name__)
    _main()
