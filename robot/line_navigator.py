import time

from gpiozero import LineSensor

import robot.components.line_tracking.robotdyn as lts

PIN_LEFT_LINE_SENSOR = 10
PIN_RIGHT_LINE_SENSOR = 9


class LineNavigator:

    def __init__(self):
        self._sensor_left = LineSensor(pin=PIN_LEFT_LINE_SENSOR,
                                       pull_up=lts.IS_PULL_UP)
        self._sensor_right = LineSensor(pin=PIN_RIGHT_LINE_SENSOR,
                                        pull_up=lts.IS_PULL_UP)

    def run(self):
        try:
            while True:
                if not self._sensor_left.is_active and not self._sensor_right.is_active:
                    print('All black!')

                elif not self._sensor_left.is_active and self._sensor_right.is_active:
                    print('Turn left')

                elif self._sensor_left.is_active and not self._sensor_right.is_active:
                    print('Turn right')

                time.sleep(0.1)

        except KeyboardInterrupt:
            pass


def _main():
    navigator = LineNavigator()
    navigator.run()


if __name__ == '__main__':
    _main()
