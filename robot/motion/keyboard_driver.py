"""Implements a Driver controlled by keyboard input.
"""
import logging

from pynput import keyboard

import robot.motion.driver as driver

_logger = logging.getLogger(__name__)

_EXIT_KEY = keyboard.Key.esc
_key_to_command = {
    # Forward
    keyboard.KeyCode.from_char('w'): driver.COMMAND_FORWARD,
    keyboard.KeyCode.from_char('W'): driver.COMMAND_FORWARD,

    # Backward
    keyboard.KeyCode.from_char('s'): driver.COMMAND_BACKWARD,
    keyboard.KeyCode.from_char('S'): driver.COMMAND_BACKWARD,

    # Left
    keyboard.KeyCode.from_char('a'): driver.COMMAND_LEFT,
    keyboard.KeyCode.from_char('A'): driver.COMMAND_LEFT,

    # Right
    keyboard.KeyCode.from_char('d'): driver.COMMAND_RIGHT,
    keyboard.KeyCode.from_char('D'): driver.COMMAND_RIGHT,

    # Turbo
    keyboard.Key.shift_l: driver.COMMAND_TURBO,
}

_instructions = """Press ESC to quit.
Use keys W, A, S, D for directions.
Hold shift for turbo.
"""


class KeyboardDriver(driver.Driver):

    def __init__(self):
        super().__init__()
        self._listener = keyboard.Listener(on_press=self._on_press,
                                           on_release=self._on_release,
                                           suppress=True)

    def _on_press(self, key):
        command = _key_to_command.get(key)
        if command is not None:
            self.set_command(command_code=command, command_value=1)

    def _on_release(self, key):
        if key == _EXIT_KEY:
            _logger.debug('Captured exit signal')
            return False

        command = _key_to_command.get(key)
        if command is not None:
            self.set_command(command_code=command, command_value=0)

    def run(self):
        print(_instructions)
        self._listener.start()
        try:
            self._listener.wait()
            _logger.info('Keyboard listener started.')
            self._listener.join()
        finally:
            self._listener.stop()
        self.close()
