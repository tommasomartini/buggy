import logging
import signal
import time

from pynput import mouse

import robot.components.servos.micro_servo_sg90 as sg90
import robot.components.servos.micro_servo_ts90a as ts90a
import robot.motion.crane.continuous_servo as cs
import robot.motion.crane.discrete_servo as ds

_instructions = """
+------------------------------------------------------------------------------+
| Crane instructions:                                                          |
| * right-click: quit                                                          |
| * left-click + drag: move left-right. Release to reset to default            |
| * mouse-wheel: move up-down                                                  |
| * wheel button: reset up-down angle to default                               |
+------------------------------------------------------------------------------+
"""

_HORIZONTAL_SERVO_PIN = 17
_VERTICAL_SERVO_PIN = 27


class MouseDrivenCrane:

    _HORIZONTAL_SENSITIVITY_px = 1
    _HORIZONTAL_SPEED_FACTOR = 1.0
    _VERTICAL_STEP_deg = 5.0

    # If no mouse event is detected in this interval of time since the last
    # event, stop the servo.
    _MAX_DELAY_BEFORE_STOP_s = 0.1

    def __init__(self, horizontal_servo, vertical_servo):
        self._horizontal_servo = horizontal_servo
        self._vertical_servo = vertical_servo

        # Catch the alarm signal that stop the motors after waiting too long
        # for the next mouse event.
        signal.signal(signal.SIGALRM, self._on_timeout)

        # When True, the crane is controlled by the mouse. When released, the
        # crane goes back to its nominal position.
        self._drag = False

        self._last_motion_time = None
        self._pos_x = None

        self._listener = mouse.Listener(on_move=self._on_move,
                                        on_click=self._on_click,
                                        on_scroll=self._on_scroll,
                                        suppress=True)

        _logger.debug('{} initialized'.format(self.__class__.__name__))

    def _on_timeout(self, signum, frame):
        self._horizontal_servo.set_speed(0)

    def _on_move(self, x, y):
        if not self._drag:
            return

        if self._last_motion_time is None:
            # Safety check in case the click event did not set the time and
            # initial positions yet.
            return

        now = time.time()
        dt = now - self._last_motion_time

        # Why the negative signs in X speed?
        # Moving the mouse to the left causes a negative dx, but the shaft
        # performs right-handed rotations. Therefore rotations to the left
        # are obtained by providing a positive velocity.
        dx = x - self._pos_x
        if abs(dx) < self._HORIZONTAL_SENSITIVITY_px:
            dx = 0
        speed_x = - self._HORIZONTAL_SPEED_FACTOR * dx / dt
        self._horizontal_servo.set_speed(speed_x)

        self._pos_x = x
        self._last_motion_time = now

        # Reset timer to trigger an alarm signal if the next mouse event
        # takes to long.
        signal.setitimer(signal.ITIMER_REAL, self._MAX_DELAY_BEFORE_STOP_s, 0)

    def _on_scroll(self, x, y, dx, dy):
        step_angle_deg = - dy * self._VERTICAL_STEP_deg
        self._vertical_servo.step(step_angle_deg)

    def _on_click(self, x, y, button, pressed):
        if button == mouse.Button.right:
            # Exit the control threads.
            self._horizontal_servo.close()
            self._vertical_servo.close()

            # Exit the mouse listener thread.
            return False

        if button == mouse.Button.left:
            if pressed:
                # Start a drag.
                self._pos_x = x
                self._pos_y = y
                self._last_motion_time = time.time()
                self._drag = True
            else:
                # End a drag.
                self._drag = False
                self._horizontal_servo.reset()

        elif button == mouse.Button.middle:
            if not pressed:
                # Reset vertical angle on release.
                self._vertical_servo.reset()

    def run(self):
        print(_instructions)
        self._listener.start()
        self._listener.wait()
        self._listener.join()


def _main():
    horizontal_servo = cs.ContinuousServo(
        pin=_HORIZONTAL_SERVO_PIN,
        max_speed_degps=sg90.MAX_OPERATING_SPEED_degps,
        min_pulse_width_s=sg90.MIN_PULSE_WIDTH_s,
        max_pulse_width_s=sg90.MAX_PULSE_WIDTH_s,
        frame_width_s=sg90.FRAME_WIDTH_s,
        nominal_max_angle_deg=sg90.MAX_ANGLE_deg,
        range_deg=None,
        default_angle_deg=0.0,
    )

    vertical_servo = ds.DiscreteServo(
        pin=_VERTICAL_SERVO_PIN,
        max_speed_degps=ts90a.MAX_OPERATING_SPEED_degps,
        min_pulse_width_s=ts90a.MIN_PULSE_WIDTH_s,
        max_pulse_width_s=ts90a.MAX_PULSE_WIDTH_s,
        frame_width_s=ts90a.FRAME_WIDTH_s,
        nominal_max_angle_deg=ts90a.MAX_ANGLE_deg,
        range_deg=[-90, 0],
        default_angle_deg=-90.,
    )

    crane = MouseDrivenCrane(horizontal_servo=horizontal_servo,
                             vertical_servo=vertical_servo)
    crane.run()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    _logger = logging.getLogger(__name__)
    _main()
