"""This module provides a base ultrasonic sensor class which provides the same
basic functionality of the DistanceSensor class in gpiozero. We had to implement
our own class to be able to drive multiple distance sensor with the same trigger
pin and thus save resources.
"""
import logging
import time

import RPi.GPIO as GPIO

_logger = logging.getLogger(__name__)

_SPEED_OF_SOUND_mps = 343.26    # m/s


class _TimeoutError(Exception):
    pass


class BaseUltrasonicSensor:
    """Implements the basic functionality to use an ultrasonic distance sensor
    like the common HC-SR04.

    Sensors like these work by sending a pulse to the TRIG pin, which triggers
    the transmitter to send out an ultrasonic signal. The sound bounces back
    and is received by the receiver, which encodes a signal to the ECHO pin,
    whose duration is equal to the time between sending the sound signal and
    receiving it back.

    Attributes:
        _trig_pin (int): TRIG pin.
        _echo_pin (int): ECHO pin.
        _pulse_s (float): Duration of the pulse to trigger a measurement,
            in seconds.
        _measure_interval_s (float): Minimum time, in seconds, between two
            consecutive measurements to guarantee clean readings.
        _name (str, optional): Name of the device.
    """

    # The formula to convert the pulse duration to distance in centimeters is:
    #   distance_cm = pulse_duration_s * speed_sound_mps * 100 / 2
    # where the x100 is to convert meters in centimeters. The pulse duration
    # equals the time from transmission to reception, that is the time
    # the sound travelled to the target and back. We divide by 2 to consider
    # the distance covered in a one-way trip.
    # This constant's unit is cm/s.
    _PULSE_TO_DISTANCE_MULTIPLIER_cmps = _SPEED_OF_SOUND_mps * 100 / 2

    # Initial setup time to allow the sensor to initialize.
    _INIT_SETUP_TIME_s = 0.01

    # We experienced some freezing when using the nominal interval. We allow for
    # some slack time between consecutive measurements.
    _MEASURE_INTERVAL_FACTOR = 1.2

    # How long to wait before giving up waiting for the signal back, in seconds.
    _TIMEOUT_s = 1.0

    # Name id.
    _id = 0

    def __init__(self,
                 trig_pin,
                 echo_pin,
                 pulse_s,
                 measure_interval_s,
                 name=None):
        self._trig_pin = trig_pin
        self._echo_pin = echo_pin
        self._pulse_s = pulse_s
        self._measure_interval_s = \
            measure_interval_s * self._MEASURE_INTERVAL_FACTOR
        self._name = name
        if self._name is None:
            self._name = 'UltrasonicSensor{}'.format(self._id)
            self._update_id()

        _logger.info('Initializing ultrasonic sensor {}'.format(self._name))

        GPIO.setup(self._trig_pin, GPIO.OUT)
        GPIO.setup(self._echo_pin, GPIO.IN)
        time.sleep(self._INIT_SETUP_TIME_s)
        GPIO.output(self._trig_pin, False)

        _logger.info('Ultrasonic sensor {} initialized'.format(self._name))

    @classmethod
    def _update_id(cls):
        cls._id += 1

    def _pulse(self):
        """Sends a pulse to the TRIG pin to start a measure.
        """
        GPIO.output(self._trig_pin, True)
        time.sleep(self._pulse_s)
        GPIO.output(self._trig_pin, False)

    def read(self):
        """Cycles forever yielding distance measurements in cm.
        """
        while True:
            self._pulse()
            try:
                channel = GPIO.wait_for_edge(self._echo_pin,
                                             GPIO.RISING,
                                             timeout=self._TIMEOUT_s)
                if channel is None:
                    raise _TimeoutError()

                pulse_start = time.time()

                channel = GPIO.wait_for_edge(self._echo_pin,
                                             GPIO.FALLING,
                                             timeout=self._TIMEOUT_s)
                if channel is None:
                    raise _TimeoutError()

                pulse_end = time.time()

                distance_cm = (pulse_end - pulse_start) \
                              * self._PULSE_TO_DISTANCE_MULTIPLIER_cmps
                yield distance_cm

            except _TimeoutError:
                _logger.warning(
                    'Ultrasonic sensor {} timed-out'.format(self._name))

            time.sleep(self._measure_interval_s)

    def close(self):
        GPIO.cleanup((self._trig_pin, self._echo_pin))
        _logger.info('Ultrasonic sensor {} shut down'.format(self._name))


def _tryout():
    GPIO.setmode(GPIO.BCM)
    sensor = BaseUltrasonicSensor(trig_pin=25,
                                  echo_pin=7,
                                  pulse_s=10e-6,
                                  measure_interval_s=60e-3)

    try:
        for distance_cm in sensor.read():
            print('Distance: {:6.2f} cm'.format(distance_cm))
    except KeyboardInterrupt:
        pass

    sensor.close()


if __name__ == '__main__':
    _tryout()
