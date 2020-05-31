import logging
import time

from gpiozero import Servo

_logger = logging.getLogger(__name__)


class ControlledServo:
    """Represents a servo motor which is driven in real time by a user.
    """

    # Minimum time to wait after commanding a movement to the servo.
    _PAUSE_s = 10e-3

    def __init__(self,
                 pin,
                 max_speed_degps,
                 min_pulse_width_s,
                 max_pulse_width_s,
                 frame_width_s,
                 nominal_max_angle_deg,
                 range_deg=None,
                 default_angle_deg=0.0):
        self._max_speed_degps = abs(max_speed_degps)
        self._nominal_max_angle_deg = abs(nominal_max_angle_deg)

        range_deg = range_deg or (-self._nominal_max_angle_deg,
                                  self._nominal_max_angle_deg)
        try:
            self._min_angle, self._max_angle = range_deg
        except TypeError:
            self._min_angle, self._max_angle = - abs(range_deg), abs(range_deg)

        if self._min_angle > self._max_angle:
            raise ValueError('Bad angle range: '
                             '[{}, {}]'.format(self._min_angle,
                                               self._max_angle))

        if self._min_angle < - self._nominal_max_angle_deg \
                or self._max_angle > self._nominal_max_angle_deg:
            raise ValueError(
                'Angle range [{}, {}] not contained in '
                'nominal range [{}, {}]'.format(self._min_angle,
                                                self._max_angle,
                                                - self._nominal_max_angle_deg,
                                                self._nominal_max_angle_deg))

        if default_angle_deg < self._min_angle \
                or default_angle_deg > self._max_angle:
            raise ValueError(
                'Provided default angle {} not in allowed range [{}, {}]'
                ''.format(default_angle_deg, self._min_angle, self._max_angle))
        self._default_angle_deg = default_angle_deg

        self._angle_deg = default_angle_deg

        initial_value = self._default_angle_deg / self._nominal_max_angle_deg
        self._servo = Servo(pin=pin,
                            initial_value=initial_value,
                            min_pulse_width=min_pulse_width_s,
                            max_pulse_width=max_pulse_width_s,
                            frame_width=frame_width_s)

        # Leave the servo the time to initialize.
        time.sleep(10 * self._PAUSE_s)
        self.reset()

    def reset(self):
        """Resets the servo to default angle.
        """
        self._servo.value = \
            self._default_angle_deg / self._nominal_max_angle_deg
        time.sleep(self._PAUSE_s)
        self._angle_deg = self._default_angle_deg

    def close(self):
        self.reset()
        self._servo.close()
