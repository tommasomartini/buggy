import time

from gpiozero import Robot
from pynput import keyboard

_KEYS_F = tuple([keyboard.KeyCode.from_char(c) for c in ('w', 'W')])
_KEYS_B = tuple([keyboard.KeyCode.from_char(c) for c in ('w', 'W')])
_KEYS_L = tuple([keyboard.KeyCode.from_char(c) for c in ('a', 'A')])
_KEYS_R = tuple([keyboard.KeyCode.from_char(c) for c in ('d', 'D')])
_KEY_TURBO = keyboard.Key.shift_l

_key_to_index = {k: idx for idx, k in enumerate([
    _KEYS_F,
    _KEYS_B,
    _KEYS_L,
    _KEYS_R,
    _KEY_TURBO,
])}

# [f, b, l, r, turbo]
_keys = [0] * 5
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
    #index = _key_to_index.get(key)
    #if index is None:


    if key in _KEYS_F:
        if _keys[0]:
            # Already set: do not do anything.
            return

        print('+f')
        _keys[0] = 1

    elif key == _KEY_TURBO:
        if _keys[1]:
            # Already set: do not do anything.
            return

        print('+t')
        _keys[1] = 1

    move()


def _on_release(key):
    if key == keyboard.Key.esc:
        return False

    if key in _KEYS_F and _keys[0]:
        print('-f')
        _keys[0] = 0

    elif key == _KEY_TURBO and _keys[1]:
        print('-t')
        _keys[1] = 0

    move()

with keyboard.Listener(on_press=_on_press, on_release=_on_release) as listener:
    listener.join()

robot.close()
print('Bye')

