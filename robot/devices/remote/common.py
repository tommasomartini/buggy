from pynput import keyboard


class Commands:
    """Collection of commands to provide a common interface between remote and
    robot.
    """
    FORWARD_ON = b'F'
    FORWARD_OFF = b'f'
    BACKWARD_ON = b'B'
    BACKWARD_OFF = b'b'
    LEFT_ON = b'L'
    LEFT_OFF = b'l'
    RIGHT_ON = b'R'
    RIGHT_OFF = b'r'
    TURBO_ON = b'T'
    TURBO_OFF = b't'
    SHUTDOWN = b's'


# Maps a key to a pair of commands to send respectively when pressing or
# releasing the associated key.
key_bindings = {
    keyboard.Key.up: (Commands.FORWARD_ON,
                      Commands.FORWARD_OFF),
    keyboard.Key.down: (Commands.BACKWARD_ON,
                        Commands.BACKWARD_OFF),
    keyboard.Key.left: (Commands.LEFT_ON,
                        Commands.LEFT_OFF),
    keyboard.Key.right: (Commands.RIGHT_ON,
                         Commands.RIGHT_OFF),
    keyboard.Key.shift: (Commands.TURBO_ON,
                         Commands.TURBO_OFF),
    keyboard.KeyCode.from_char('q'): (None, Commands.SHUTDOWN),
}
