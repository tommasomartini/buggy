import logging
import threading

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

        # A Driver exposes two Events objects that external objects can use
        # to signal the need of an emergency stops and the cease of the
        # safety stop condition.
        # This class has the authority to clear only the "dismiss" Event, but
        # it is up to the caller to clear the safety stop Event.
        self._engage_safety_stop_event = threading.Event()
        self._dismiss_safety_stop_event = threading.Event()

        # This thread listens to the events notifying the need of a safety
        # stop.
        self._safety_stop_thread = threading.Thread(target=self._safety_stop,
                                                    name='SafetyStopListener',
                                                    daemon=True)
        self._safety_stop_thread.start()

    def _safety_stop(self):
        """Listens to the Events to engage and dismiss a safety stop condition.
        Function to be used as a Thread target.

        On safety stop request, stops the robot and resets all the commands.
        """
        while True:
            self._engage_safety_stop_event.wait()

            # Stop the robot and reset all the commands.
            self._robot.stop()
            for idx in range(len(self._commands)):
                self._commands[idx] = 0
            _logger.debug('Safety stop engaged')

            self._dismiss_safety_stop_event.wait()
            self._dismiss_safety_stop_event.clear()
            _logger.debug('Safety stop dismissed')

    def _move(self):
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
                self._robot.forward(**kwargs)
                _logger.debug('Move forward with arguments: {}'.format(kwargs))
            elif self._commands[COMMAND_BACKWARD]:
                self._robot.backward(**kwargs)
                _logger.debug('Move backward with arguments: {}'.format(kwargs))

    def set_command(self, command_code, command_value):
        """Receives an external command, stores it and processes it.

        Args:
            command_code (int): What command to execute.
            command_value (int): The value associated with this command. Many
                times it is a 1 to set or a 0 to cancel it.
        """
        if self._engage_safety_stop_event.is_set():
            # Ignore every command until it is safe to proceed.
            return

        if command_code < 0 or command_code >= len(self._commands):
            # Unrecognized command.
            _logger.warning('Unrecognized command code: '
                            '{}'.format(command_code))
            return

        if self._commands[command_code] == command_value:
            # Command already set: no need to do anything.
            return

        # Set this command and execute.
        self._commands[command_code] = command_value
        self._move()

    @property
    def engage_safety_stop_event(self):
        return self._engage_safety_stop_event

    @property
    def dismiss_safety_stop_event(self):
        return self._dismiss_safety_stop_event

    def close(self):
        self._robot.close()
