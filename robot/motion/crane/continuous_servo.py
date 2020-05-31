import logging
import threading
import time

import robot.motion.crane.controlled_servo as cs

_logger = logging.getLogger(__name__)


class ContinuousServo(cs.ControlledServo):

    _MIN_STEP_SIZE_deg = 1.0

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

        # Right-handed angular rotation of the shaft requested by the user.
        self._speed_degps = 0
        _logger.debug('{} initialized'.format(self.__class__.__name__))

        self._control_thread = threading.Thread(target=self._move,
                                                name='ServoControl',
                                                daemon=True)
        self._control_thread.start()

    def _move(self):
        """Function run by the thread controlling the actual movement.

        This function rotates the servo's shaft with a certain speed.
        """
        while self._speed_degps is not None:
            if self._speed_degps == 0:
                # Do not move the servo.
                time.sleep(self._PAUSE_s)
                continue

            step_deg = self._speed_degps * self._PAUSE_s
            if abs(step_deg) < self._MIN_STEP_SIZE_deg:
                # Too slow of a movement to perform it.
                time.sleep(self._PAUSE_s)
                continue

            self._angle_deg = max(self._min_angle,
                                  min(self._max_angle,
                                      self._angle_deg + step_deg))

            # In most servos a positive value corresponds to the right-handed
            # positive rotation of the shaft.
            self._servo.value = self._angle_deg / self._nominal_max_angle_deg
            time.sleep(self._PAUSE_s)

        self.reset()
        self._servo.close()

        _logger.debug('{} stopped'.format(self.__class__.__name__))

    def reset(self):
        # Set the speed to zero asap to prevent the control thread from moving
        # the servo.
        self._speed_degps = 0
        super().reset()

    def set_speed(self, speed_degps):
        """Sets the speed to rotate the servo's shaft.

        Args:
            speed_degps (float): Speed in degrees per second. None to stop
                the control thread.
        """
        self._speed_degps = max(- self._max_speed_degps,
                                min(self._max_speed_degps, speed_degps))

    def close(self):
        # Set the direction to None to stop the control thread.
        self._speed_degps = None
