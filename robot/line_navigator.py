import enum
import logging
import time

from gpiozero import LineSensor

import robot.components.line_tracking.robotdyn as lts
import robot.motion.driver as dvr

PIN_LEFT_LINE_SENSOR = 10
PIN_RIGHT_LINE_SENSOR = 9

_logger = logging.getLogger(__name__)


class LineNavigator:

    # Time interval between subsequent sensors readings.
    _FRAME_RATE_s = 0.001

    class _State(enum.Enum):
        LEFT_ON_TRACK = 0
        RIGHT_ON_TRACK = 1
        BOTH_ON_TRACK = 2
        NONE_ON_TRACK = 3

    def __init__(self,
                 left_on_track_callback=None,
                 right_on_track_callback=None,
                 both_on_track_callback=None,
                 none_on_track_callback=None):
        self._sensor_left = LineSensor(pin=PIN_LEFT_LINE_SENSOR,
                                       pull_up=lts.IS_PULL_UP)
        self._sensor_right = LineSensor(pin=PIN_RIGHT_LINE_SENSOR,
                                        pull_up=lts.IS_PULL_UP)

        # These callback functions are called the first time that one of the
        # relative events occurs.
        self._callbacks = {
            self._State.BOTH_ON_TRACK: both_on_track_callback,
            self._State.LEFT_ON_TRACK: left_on_track_callback,
            self._State.RIGHT_ON_TRACK: right_on_track_callback,
            self._State.NONE_ON_TRACK: none_on_track_callback,
        }

        # Assume the robot is well-centered on the track.
        self._state = self._State.NONE_ON_TRACK

    def run(self):
        try:
            while True:

                # Active sensor means that the track was detected.
                left = not self._sensor_left.is_active
                right = not self._sensor_right.is_active

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

        self._sensor_left.close()
        self._sensor_right.close()
        _logger.info('{} closed'.format(self.__class__.__name__))


def _main():
    driver = dvr.Driver()

    def _straight_ahead():
        # Reset forward direction.
        driver.set_command(command_code=dvr.COMMAND_RIGHT, command_value=False)
        driver.set_command(command_code=dvr.COMMAND_LEFT, command_value=False)
        driver.set_command(command_code=dvr.COMMAND_FORWARD, command_value=True)

    def _turn_left():
        driver.set_command(command_code=dvr.COMMAND_LEFT, command_value=True)

    def _turn_right():
        driver.set_command(command_code=dvr.COMMAND_RIGHT, command_value=True)

    def _stop():
        driver.stop()

    navigator = LineNavigator(left_on_track_callback=_turn_left,
                              right_on_track_callback=_turn_right,
                              both_on_track_callback=_stop,
                              none_on_track_callback=_straight_ahead)
    driver.set_command(command_code=dvr.COMMAND_FORWARD, command_value=True)
    navigator.run()


if __name__ == '__main__':
    _main()
