import enum
import logging
import time

from gpiozero import LineSensor

import robot.components.line_tracking.robotdyn as lts
import robot.devices.led_status as ls
import robot.motion.driver as dvr

PIN_LEFT_LINE_SENSOR = 10
PIN_RIGHT_LINE_SENSOR = 9

_logger = logging.getLogger(__name__)


class LineNavigator:

    # Time interval between subsequent sensor readings.
    _FRAME_RATE_s = 0.001

    class _State(enum.Enum):
        LEFT_ON_TRACK = 0
        RIGHT_ON_TRACK = 1
        BOTH_ON_TRACK = 2
        NONE_ON_TRACK = 3

    def __init__(self, driver, status_led, black_track=True):
        self._driver = driver
        self._status_led = status_led
        self._black_track = black_track

        self._sensor_left = LineSensor(pin=PIN_LEFT_LINE_SENSOR,
                                       pull_up=lts.IS_PULL_UP)
        self._sensor_right = LineSensor(pin=PIN_RIGHT_LINE_SENSOR,
                                        pull_up=lts.IS_PULL_UP)

        # These callback functions are called the first time that one of the
        # relative events occurs.
        self._callbacks = {
            self._State.BOTH_ON_TRACK: self._both_on_track_callback,
            self._State.LEFT_ON_TRACK: self._left_on_track_callback,
            self._State.RIGHT_ON_TRACK: self._right_on_track_callback,
            self._State.NONE_ON_TRACK: self._none_on_track_callback,
        }

        # Assume the robot is well-centered on the track.
        self._state = self._State.NONE_ON_TRACK

        self._status_led.set(ls.Status.AUTOPILOT)

    def _none_on_track_callback(self):
        # Reset forward direction.
        self._driver.set_command(command_code=dvr.COMMAND_RIGHT,
                                 command_value=False)
        self._driver.set_command(command_code=dvr.COMMAND_LEFT,
                                 command_value=False)
        self._driver.set_command(command_code=dvr.COMMAND_FORWARD,
                                 command_value=True)

    def _left_on_track_callback(self):
        self._driver.set_command(command_code=dvr.COMMAND_LEFT,
                                 command_value=True)

    def _right_on_track_callback(self):
        self._driver.set_command(command_code=dvr.COMMAND_RIGHT,
                                 command_value=True)

    def _both_on_track_callback(self):
        self._driver.stop()
        _logger.warning('Both line sensors detected a line: stop the motors')

    def run(self):
        # Start the robot.
        self._driver.set_command(command_code=dvr.COMMAND_FORWARD,
                                 command_value=True)

        try:
            while True:

                # Active sensor means that the track was detected.
                if self._black_track:
                    left = not self._sensor_left.is_active
                    right = not self._sensor_right.is_active
                else:
                    left = self._sensor_left.is_active
                    right = self._sensor_right.is_active

                if left and right:
                    new_state = self._State.BOTH_ON_TRACK

                elif left and not right:
                    new_state = self._State.LEFT_ON_TRACK

                elif not left and right:
                    new_state = self._State.RIGHT_ON_TRACK

                else:
                    new_state = self._State.NONE_ON_TRACK

                if new_state != self._state:
                    self._state = new_state
                    callback = self._callbacks[self._state]
                    if callback is not None:
                        callback()

                time.sleep(self._FRAME_RATE_s)

        except KeyboardInterrupt:
            pass

        finally:
            self.close()

    def close(self):
        self._sensor_left.close()
        self._sensor_right.close()
        _logger.info('{} closed'.format(self.__class__.__name__))
