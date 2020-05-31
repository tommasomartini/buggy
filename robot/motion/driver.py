"""Base class to control them motors by providing single commands.

Example (drive forward for one second and then stop):
    import time
    driver = Driver()
    driver.set_command(COMMAND_FORWARD, 1)
    time.sleep(1)
    driver.set_command(COMMAND_FORWARD, 0)
    driver.close()
"""

import logging
import multiprocessing as mp

from gpiozero import Robot

_logger = logging.getLogger(__name__)

# The Raspberry Pi 4B provides only 4 pins with hardware-driven PWM and these
# are pins 12, 13, 18 and 19. However, pins 12-18 and 13-19 are driven by
# the same modulator, therefore we group them together.
_LEFT_MOTOR_POS_PIN = 12
_LEFT_MOTOR_NEG_PIN = 18
_RIGHT_MOTOR_POS_PIN = 19
_RIGHT_MOTOR_NEG_PIN = 13

# Codes to pilot the driver.
COMMAND_FORWARD = 0
COMMAND_BACKWARD = 1
COMMAND_LEFT = 2
COMMAND_RIGHT = 3
COMMAND_TURBO = 4


class Driver:
    """Controls the motors and the motion direction and speed.
    """
    _NORMAL_SPEED = 0.5
    _TURBO_SPEED = 1.0

    def __init__(self):
        self._commands = [
            0,  # forward
            0,  # backward
            0,  # left
            0,  # right
            0,  # turbo
        ]

        self._robot = Robot(left=(_LEFT_MOTOR_NEG_PIN,
                                  _LEFT_MOTOR_POS_PIN),
                            right=(_RIGHT_MOTOR_POS_PIN,
                                   _RIGHT_MOTOR_NEG_PIN))

        # A Driver exposes a number of multiprocess Events objects that
        # external objects can use to signal the need of an emergency stops.
        # It is up to the caller to clear the safety stop Event.
        self._safety_stop_event = mp.Event()
        self._safety_stop_forward_event = mp.Event()
        self._safety_stop_backward_event = mp.Event()

    def _move(self):
        if self._safety_stop_event.is_set():
            if self._robot.left_motor.is_active or self._robot.right_motor.is_active:
                # Both motors must be completely still.
                self._robot.stop()

            # Not further actions allowed in case of full safety stop.
            return

        # In case of forward/backward safety stop, motors cannot spin in the
        # same forbidden direction. At most one is allowed to let the robot
        # spin in place.
        if self._safety_stop_forward_event.is_set():
            if self._robot.left_motor.value > 0 and self._robot.right_motor.value > 0:
                self._robot.stop()
                return

        if self._safety_stop_backward_event.is_set():
            if self._robot.left_motor.value < 0 and self._robot.right_motor.value < 0:
                self._robot.stop()
                return

        _logger.debug('Execute commands: {}'.format(self._commands))

        if sum(self._commands[:4]) == 0:
            # All the motion commands are unset: stop the motors.
            _logger.debug('Stop all motors')
            self._robot.stop()
            return

        # Setting both "forward" and "backward" or "left" and "right"
        # is not allowed. Maintain the current course.
        if (self._commands[COMMAND_FORWARD] and
            self._commands[COMMAND_BACKWARD]) or \
                (self._commands[COMMAND_LEFT] and
                 self._commands[COMMAND_RIGHT]):
            _logger.warning('Invalid command configuration')
            return

        speed = self._TURBO_SPEED if self._commands[COMMAND_TURBO] \
            else self._NORMAL_SPEED

        if not self._commands[COMMAND_FORWARD] and \
                not self._commands[COMMAND_BACKWARD]:
            # Only left-right commands provided.
            if self._commands[COMMAND_LEFT]:
                self._robot.left(speed)
                _logger.debug('Turn left with speed {}'.format(speed))
            elif self._commands[COMMAND_RIGHT]:
                self._robot.right(speed)
                _logger.debug('Turn right with speed {}'.format(speed))
            else:
                assert False, 'Reached unexpected condition'
        else:
            # Move forward or backward, possible also turning left or right.
            kwargs = dict(speed=speed)

            # We already checked that left and right cannot be set together.
            if self._commands[COMMAND_LEFT]:
                kwargs['curve_left'] = 0.5
            elif self._commands[COMMAND_RIGHT]:
                kwargs['curve_right'] = 0.5

            # We already checked that forward and backward cannot
            # be set together.
            if self._commands[COMMAND_FORWARD]:
                if self._safety_stop_forward_event.is_set():
                    _logger.debug('Cannot execute: forward safety stop set')
                    return
                self._robot.forward(**kwargs)
                _logger.debug('Move forward with arguments: {}'.format(kwargs))
            elif self._commands[COMMAND_BACKWARD]:
                if self._safety_stop_backward_event.is_set():
                    _logger.debug('Cannot execute: backward safety stop set')
                    return
                self._robot.backward(**kwargs)
                _logger.debug('Move backward with arguments: {}'.format(kwargs))

    def set_command(self, command_code, command_value):
        """Receives an external command, stores it and processes it.

        Args:
            command_code (int): What command to execute.
            command_value (int): The value associated with this command. Many
                times it is a 1 to set or a 0 to cancel it.
        """
        if command_code < 0 or command_code >= len(self._commands):
            # Unrecognized command.
            _logger.warning('Unrecognized command code: '
                            '{}'.format(command_code))
            return

        self._commands[command_code] = command_value
        self._move()

    def stop(self):
        """Stops all the motors at the same time.
        """
        for idx in range(len(self._commands)):
            self._commands[idx] = 0
        self._move()

    @property
    def safety_stop_event(self):
        return self._safety_stop_event

    @property
    def safety_stop_forward_event(self):
        return self._safety_stop_forward_event

    @property
    def safety_stop_backward_event(self):
        return self._safety_stop_backward_event

    def close(self):
        self._robot.stop()
        self._robot.close()
        _logger.debug('Shut down {}'.format(self.__class__.__name__))
