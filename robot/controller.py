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
    return
    
    # Evaluate the commands provided and set the motors.
    if sum(_keys[:4]) == 0:
        # Nothing to do.
        robot.stop()
        return

    # direction = 
    # Move forward. But how fast?
    speed = 0.5 + _keys[1] * 0.5
    robot.forward(speed)


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

