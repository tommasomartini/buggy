import logging
import threading
import time

from gpiozero import DistanceSensor, LED, Robot
from pynput import keyboard

logging.basicConfig(level=logging.DEBUG, style='{', format='[{threadName}][{name}][{levelname}] {message}')
_logger = logging.getLogger(__name__)


_key_to_index = {
    # Forward
    keyboard.KeyCode.from_char('w'): 0,
    keyboard.KeyCode.from_char('W'): 0,
    
    # Backward
    keyboard.KeyCode.from_char('s'): 1,
    keyboard.KeyCode.from_char('S'): 1,

    # Left
    keyboard.KeyCode.from_char('a'): 2,
    keyboard.KeyCode.from_char('A'): 2,
    
    # Right
    keyboard.KeyCode.from_char('d'): 3,
    keyboard.KeyCode.from_char('D'): 3,
    
    # Turbo
    keyboard.Key.shift_l: 4,
}
_commands = [0] * len(set(_key_to_index.values()))

_engage_safety_stop_event = threading.Event()
_dismiss_safety_stop_event = threading.Event()
_mv_time = 1.

# Devices
robot = Robot(left=(18, 12), right=(19, 13))
led = LED(17)


def _when_in_range():
    _logger.debug('Obstacle in range')
    _engage_safety_stop_event.set()
    led.blink(on_time=0.1, off_time=0.1)


def _when_out_of_range():
    _logger.debug('Clear way')
    _engage_safety_stop_event.clear()
    _dismiss_safety_stop_event.set()
    led.off()


distance_sensor = DistanceSensor(echo=7, trigger=25, threshold_distance=5e-2)
distance_sensor.when_in_range = _when_in_range
distance_sensor.when_out_of_range = _when_out_of_range


def _safety_stop():
    while True:
        _engage_safety_stop_event.wait()
        _logger.debug('Emergency stop!')

        # Stop the robot and reset all the commands.
        robot.stop()
        for idx in range(4):
            _commands[idx] = 0

        _dismiss_safety_stop_event.wait()
        _logger.debug('Dismiss emergency stop')
        _dismiss_safety_stop_event.clear()


safety_stop_thread = threading.Thread(target=_safety_stop, name='safety_stop', daemon=True)
safety_stop_thread.start()


def move():
    _logger.debug('Move. Commands: {}'.format(_commands))

    if sum(_commands[:4]) == 0:
        # No move action to perform.
        _logger.debug(' Stop')
        robot.stop()
        return

    # Setting both "forward" and "backward" or "left" and "right" not allowed.
    # Maintain the current course.
    if (_commands[0] and _commands[1]) or (_commands[2] and _commands[3]):
        _logger.debug(' Invalid command configuration')
        return

    speed = 1.0 if _commands[4] else 0.5

    if (not _commands[0]) and (not _commands[1]):
        # Only left-right provided.
        _logger.debug(' Only left-right')
        mv_func = robot.left if _commands[2] else robot.right
        # assert _commands[3]
        mv_func(speed)
    else:
        _logger.debug(' Forward-backward')
        mv_func = robot.forward if _commands[0] else robot.backward

        # Any lateral movement?
        kwargs = dict(speed=speed)
        if _commands[2]:
            _logger.debug('  + left')
            kwargs['curve_left'] = 0.5
        if _commands[3]:
            _logger.debug('  + right')
            kwargs['curve_right'] = 0.5

        mv_func(**kwargs)

    _logger.debug('--- end move() ---')


def _set_command(key, value):
    if _engage_safety_stop_event.is_set():
        # Ignore every command until it is safe to proceed.
        return

    index = _key_to_index.get(key)
    if index is None:
        # Unrecognized command.
        return

    if _commands[index] == value:
        # Command already set: no need to do anything.
        return

    # Set this command.
    _commands[index] = value

    move()


def _on_press(key):
    index = _key_to_index.get(key)
    if index is None:
        return
    _set_command(key, 1)


def _on_release(key):
    if key == keyboard.Key.esc:
        return False
    _set_command(key, 0)


with keyboard.Listener(on_press=_on_press,
                       on_release=_on_release,
                       suppress=True) as listener:
    listener.join()

led.off()
led.close()
distance_sensor.close()
robot.close()
print('Bye')

