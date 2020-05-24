"""This module provides a base ultrasonic sensor class which provides the same
basic functionality of the DistanceSensor class in gpiozero.
We had to implement our own class for two reasons:
* the PlayKnowLogy ultrasonic sensor seems to behave slightly differently than
  the standard HC-SR04, hence it is not compatible with the gpiozero class;
* we want to able to drive multiple sensors simultaneously using the same
  trigger pin to save resources.
"""
import logging
import time

import RPi.GPIO as GPIO

_logger = logging.getLogger(__name__)

_SPEED_OF_SOUND_mps = 343.26    # m/s


class _TimeoutError(Exception):
    pass


class UltrasonicSensor:
    """Implements the basic functionality to use an ultrasonic distance sensor
    like the common HC-SR04.

    Sensors like these work by sending a pulse to the TRIG pin, which triggers
    the transmitter to send out an ultrasonic signal. The sound bounces back
    and is received by the receiver, which encodes a signal to the ECHO pin,
    whose duration is equal to the time between sending the sound signal and
    receiving it back.

    This class provides two callback functions to call when an obstacle gets in
    range or out of range. The functions are blocking: while the functions do
    not return, no further measurement will be taken.

    Attributes:
        _trig_pin (int): TRIG pin.
        _echo_pin (int): ECHO pin.
        _pulse_s (float): Duration of the pulse to trigger a measurement,
            in seconds.
        _measure_interval_s (float): Minimum time, in seconds, between two
            consecutive measurements to guarantee clean readings.
        _distance_threshold_m (float, optional): Distance in meters. When the
            read distance becomes lower than this threshold, the callback
            "when_in_range" is called. When the read distance becomes bigger,
            the "when_out_of_rage" is called.
        _when_in_range (callable, optional): Function to call when the read
            distance becomes smaller than "_distance_threshold_m".
        _when_out_of_range (callable, optional): Function to call when the read
            distance becomes larger than "_distance_threshold_m".
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
    _TIMEOUT_s = 1

    # Name id.
    _id = 0

    def __init__(self,
                 trig_pin,
                 echo_pin,
                 pulse_s,
                 measure_interval_s,
                 distance_threshold_m=None,
                 when_in_range=None,
                 when_out_of_range=None,
                 name=None):
        self._trig_pin = trig_pin
        self._echo_pin = echo_pin
        self._pulse_s = pulse_s
        self._measure_interval_s = \
            measure_interval_s * self._MEASURE_INTERVAL_FACTOR
        self._distance_threshold_m = distance_threshold_m
        self._when_in_range = when_in_range
        self._when_out_of_range = when_out_of_range
        self._name = name
        if self._name is None:
            self._name = 'UltrasonicSensor{}'.format(self._id)
            self._update_id()

        # Keeps track if the measured distance is in range or not.
        self._in_range = None

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

    def _callbacks(self, distance_cm):
        """Calls the appropriate callback function, if a status change is
        detected.

        Args:
            distance_cm (float): The latest read distance, in cm.
        """
        if self._distance_threshold_m is None:
            return

        if self._when_in_range is None and self._when_out_of_range is None:
            return

        in_range = distance_cm <= 100 * self._distance_threshold_m
        if in_range == self._in_range:
            # No status change.
            return

        # Detected a status change.
        self._in_range = in_range

        if self._in_range:
            # Out of -> in range.
            if self._when_in_range is not None:
                self._when_in_range()
        else:
            # In -> out of range.
            if self._when_out_of_range is not None:
                self._when_out_of_range()

    def read(self):
        """Cycles forever yielding distance measurements in cm.
        """
        # The GPIO library requires ms as units.
        timeout_ms = int(1000 * self._TIMEOUT_s)
        while True:
            self._pulse()
            try:
                channel = GPIO.wait_for_edge(self._echo_pin,
                                             GPIO.RISING,
                                             timeout=timeout_ms)
                if channel is None:
                    raise _TimeoutError()

                pulse_start = time.time()
                channel = GPIO.wait_for_edge(self._echo_pin,
                                             GPIO.FALLING,
                                             timeout=timeout_ms)
                if channel is None:
                    raise _TimeoutError()

                pulse_end = time.time()
                distance_cm = (pulse_end - pulse_start) \
                              * self._PULSE_TO_DISTANCE_MULTIPLIER_cmps
                yield distance_cm
                self._callbacks(distance_cm=distance_cm)

            except _TimeoutError:
                _logger.warning(
                    'Ultrasonic sensor {} timed-out'.format(self._name))

            time.sleep(self._measure_interval_s)

    def close(self):
        GPIO.cleanup((self._trig_pin, self._echo_pin))
        _logger.info('Ultrasonic sensor {} shut down'.format(self._name))


def _tryout():
    GPIO.setmode(GPIO.BCM)
    sensor = UltrasonicSensor(
        trig_pin=25,
        echo_pin=8,
        pulse_s=10e-6,                                  # 10 us
        measure_interval_s=60e-3,                       # 60 ms
        distance_threshold_m=0.1,                       # 10 cm
        when_in_range=lambda: print('In range'),
        when_out_of_range=lambda: print('Out of range'),
        name='MySonar')

    try:
        for distance_cm in sensor.read():
            print('Distance: {:6.2f} cm'.format(distance_cm))
    except KeyboardInterrupt:
        pass

    sensor.close()


if __name__ == '__main__':
    _tryout()
