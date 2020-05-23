import time

from gpiozero import Robot
from pynput import keyboard

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

_mv_time = 1.

robot = Robot(left=(18, 12), right=(19, 13))


def move():
    # Evaluate the commands provided and set the motors.
    if sum(_commands[:4]) == 0:
        # Nothing to do.
        robot.stop()
        return

    # Setting both "forward" and "backward" or "left" and "right" not allowed.
    # Maintain the current course.
    if (_commands[0] and _commands[1]) or (_commands[2] and _commands[3]):
        return

    speed = 1.0 if _commands[4] else 0.5

    if not _commands[0] and not _commands[1]:
        # Only left-right provided.
        mv_func = robot.left if _commands[2] else robot.right
        mv_func(speed)
    else:
        mv_func = robot.forward if _commands[0] else robot.backward

        # Any lateral movement?
        kwargs = dict(speed=speed)
        if _commands[2]:
            kwargs['curve_left'] = 0.5
        elif _commands[3]:
            kwargs['curve_right'] = 0.5

        mv_func(**kwargs)


def _on_press(key):
    index = _key_to_index.get(key)
    if index is None:
        return

    if _commands[index]:
        # Command already set: no need to do anything.
        return

    # Set this command.
    _commands[index] = 1

    print('+{}'.format(index))

    move()


def _on_release(key):
    if key == keyboard.Key.esc:
        return False

    index = _key_to_index.get(key)
    if index is None:
        return

    # Unset this command.
    _commands[index] = 0

    print('-{}'.format(index))

    move()


with keyboard.Listener(on_press=_on_press,
                       on_release=_on_release,
                       suppress=True) as listener:
    listener.join()

robot.close()
print('Bye')

