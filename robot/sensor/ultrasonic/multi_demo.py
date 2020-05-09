import logging
import threading
import time

import RPi.GPIO as GPIO

TRIG_PIN = 17

# From documentation:
#   https://www.robotshop.com/media/files/pdf/hc-sr05-ultrasonic-range-finder-datasheet.pdf
_PULSE_DURATION_s = 10e-6       # 10 microseconds
# It is recommended to trigger at most every 60 ms.
_MEASURE_INTERVAL_s = 60e-3

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


class _UltrasonicSensor(threading.Thread):

    def __init__(self,
                 echo_pin,
                 is_pull_up,
                 lock,
                 **kwargs):
        super().__init__(**kwargs)
        self._echo_pin = echo_pin
        self._is_pull_up = is_pull_up
        self._lock = lock
        self._value = None

        GPIO.setup(self._echo_pin, GPIO.IN)

    def run(self):
        while True:
            # Record the time when the pulse is received back and calculate
            # the target distance.
            while GPIO.input(self._echo_pin) == (not self._is_pull_up):
                pass
            pulse_start = time.time()
            while GPIO.input(self._echo_pin) == self._is_pull_up:
                pass
            pulse_duration = time.time() - pulse_start
            distance_cm = pulse_duration * _PULSE_TO_DISTANCE_MULTIPLIER_cmps

            # New pulse detected: acquire the lock and write it down.
            with self._lock:
                self._value = distance_cm

    @property
    def value(self):
        return self._value

    @property
    def lock(self):
        return self._lock


class UltrasonicSensorDriver:

    def __init__(self, trig_pin, sensors_params):
        num_sensors = len(sensors_params)
        if num_sensors == 0:
            _logger.warning('No ultrasonic sensor provided to driver')

        echo_pins = {params['echo_pin'] for params in sensors_params}
        if len(echo_pins) != num_sensors:
            raise ValueError('Echo pins are not unique')

        sensor_names = {params['name'] for params in sensors_params}
        if len(sensor_names) != num_sensors:
            raise ValueError('Sensor names are not unique')

        self._trig_pin = trig_pin
        GPIO.setup(self._trig_pin, GPIO.OUT)

        self._sensors = [
            _UltrasonicSensor(echo_pin=params['echo_pin'],
                              is_pull_up=params['is_pull_up'],
                              name=params['name'],
                              lock=threading.Lock())
            for params in sensors_params
        ]

        _logger.info('Ultrasonic sensor driver ready')

    def _trigger(self):
        """Trigger the pulse."""
        GPIO.output(self._trig_pin, True)
        time.sleep(_PULSE_DURATION_s)
        GPIO.output(self._trig_pin, False)

    def read(self):
        if len(self._sensors) == 0:
            raise ValueError('Tried to read from ultrasonic sensor driver '
                             'with no sensor set')

        # Start the sensor threads and pause to let them time to set up.
        for sensor in self._sensors:
            sensor.start()
        time.sleep(1e-2)    # 10 ms should be enough

        GPIO.output(self._trig_pin, False)
        while True:
            # Generate the pulse.
            self._trigger()

            # Wait for all of the sensor to collect data.
            time.sleep(_EFFECTIVE_MEASURE_INTERVAL_s)

            # Yield the readings.
            readings = {}
            for sensor in self._sensors:
                with sensor.lock:
                    readings[sensor.name] = sensor.value
            yield readings


def _main():
    GPIO.setmode(GPIO.BCM)

    sensors_params = [
        dict(echo_pin=27,
             is_pull_up=True,
             name='HC-SR04'),
        dict(echo_pin=18,
             is_pull_up=False,
             name='HC-SR05'),
    ]
    driver = UltrasonicSensorDriver(trig_pin=TRIG_PIN,
                                    sensors_params=sensors_params)

    try:
        for readings in driver.read():
            for sensor_name, sensor_reading in readings.items():
                print('{}: {:6.2f} cm'.format(sensor_name, sensor_reading))
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()

    print('Bye!')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    _logger = logging.getLogger(__name__)
    _main()
