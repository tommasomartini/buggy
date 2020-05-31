import logging
import time

import robot.motion.crane.controlled_servo as cs

_logger = logging.getLogger(__name__)


class DiscreteServo(cs.ControlledServo):
    """Represents a controlled servo moving by discrete steps. The user controls
    the servo by providing the next angular step to perform.
    """

    def __init__(self,
                 pin,
                 max_speed_degps,
                 min_pulse_width_s,
                 max_pulse_width_s,
                 frame_width_s,
                 nominal_max_angle_deg,
                 range_deg=None,
                 default_angle_deg=0.0):
        super().__init__(pin=pin,
                         max_speed_degps=max_speed_degps,
                         min_pulse_width_s=min_pulse_width_s,
                         max_pulse_width_s=max_pulse_width_s,
                         frame_width_s=frame_width_s,
                         nominal_max_angle_deg=nominal_max_angle_deg,
                         range_deg=range_deg,
                         default_angle_deg=default_angle_deg)

        _logger.debug('{} initialized'.format(self.__class__.__name__))

    def step(self, step_angle_deg):
        if step_angle_deg == 0:
            return

        self._angle_deg = max(self._min_angle,
                              min(self._max_angle,
                                  self._angle_deg + step_angle_deg))

        # In most servos a positive value corresponds to the right-handed
        # positive rotation of the shaft.
        self._servo.value = self._angle_deg / self._nominal_max_angle_deg
        time.sleep(self._PAUSE_s)

    def close(self):
        self.reset()
        self._servo.close()
