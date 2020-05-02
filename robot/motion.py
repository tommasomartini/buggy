from pynput import keyboard

is_going = False

_GO_KEY = keyboard.Key.up


def on_press(key):
    global is_going
    if key == _GO_KEY:
        if not is_going:
            is_going = True
            print('Start')


def on_release(key):
    global is_going
    if key == keyboard.Key.esc:
        # Stop listener.
        is_going = False
        return False

    if key == _GO_KEY:
        is_going = False
        print('Stop')

# Collect events until released

with keyboard.Listener(
        on_press=on_press,
        on_release=on_release) as listener:
    listener.join()

# ...or, in a non-blocking fashion:
listener = keyboard.Listener(
    on_press=on_press,
    on_release=on_release)
listener.start()
