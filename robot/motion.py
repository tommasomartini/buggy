from gpiozero import Robot
import time
from pynput import keyboard

print('Start')

robby = Robot(left=(7, 8), right=(9, 10))
is_going = False
_FW_KEY = keyboard.Key.up
_BW_KEY = keyboard.Key.down
_L_KEY = keyboard.Key.left
_R_KEY = keyboard.Key.right


def on_press(key):
    global is_going
    if key == _FW_KEY:
        if not is_going:
            is_going = True
            #print('Start')
            robby.forward()
    elif key == _BW_KEY:
        robby.backward()
    elif key == _L_KEY:
        robby.left()
    elif key == _R_KEY:
        robby.right()


def on_release(key):
    global is_going
    if key == keyboard.Key.esc:
        # Stop listener.
        is_going = False
        robby.stop()
        return False

    if key in (_FW_KEY, _BW_KEY, _L_KEY, _R_KEY):
        is_going = False
        robby.stop()
        # print('Stop')

# Collect events until released

with keyboard.Listener(
        on_press=on_press,
        on_release=on_release) as listener:
    listener.join()

robby.stop()

