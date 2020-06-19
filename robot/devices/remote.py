import logging

from pynput import keyboard

import common.network as network
import robot.motion.driver as dvr

_logger = logging.getLogger(__name__)


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


_key_bindings = {
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
}

_instructions = """Press ESC to quit.
Use the arrow keys to move.
Hold shift for turbo.
"""


class RemoteSender:
    """Remote controller on user's side.

    The remote sends raw signals: it is up to the receiver to interpret them.
    """

    def __init__(self):
        self._client = network.UDPClient(ip=network.RASPBERRYPI_HOSTNAME,
                                         port=network.PORT)

    def _on_press(self, key):
        data_byte = _key_bindings.get(key, None)
        if data_byte is not None:
            self._client.send(data_byte[0])

    def _on_release(self, key):
        if key == keyboard.Key.esc:
            return False

        data_byte = _key_bindings.get(key, None)
        if data_byte is not None:
            self._client.send(data_byte[1])

    def run(self):
        _logger.debug('{} started'.format(self.__class__.__name__))

        print(_instructions)
        listener = keyboard.Listener(on_press=self._on_press,
                                     on_release=self._on_release,
                                     suppress=True)

        listener.start()
        try:
            listener.wait()
            listener.join()
        finally:
            listener.stop()

        self._client.close()

        _logger.debug('{} stopped'.format(self.__class__.__name__))


class RemoteReceiver:
    """Remote controller on robot's side: receives signals from the sender at
    user's side.
    """

    def __init__(self, driver):
        self._driver = driver
        self._server = network.UDPServer(ip=network.RASPBERRYPI_HOSTNAME,
                                         port=network.PORT)

    def run(self):
        _logger.debug('{} started'.format(self.__class__.__name__))

        try:
            for data_byte in self._server.receive():
                if data_byte == Commands.FORWARD_ON:
                    self._driver.set_command(command_code=dvr.COMMAND_FORWARD,
                                             command_value=True)
                elif data_byte == Commands.FORWARD_OFF:
                    self._driver.set_command(command_code=dvr.COMMAND_FORWARD,
                                             command_value=False)
                elif data_byte == Commands.BACKWARD_ON:
                    self._driver.set_command(command_code=dvr.COMMAND_BACKWARD,
                                             command_value=True)
                elif data_byte == Commands.BACKWARD_OFF:
                    self._driver.set_command(command_code=dvr.COMMAND_BACKWARD,
                                             command_value=False)
                elif data_byte == Commands.LEFT_ON:
                    self._driver.set_command(command_code=dvr.COMMAND_LEFT,
                                             command_value=True)
                elif data_byte == Commands.LEFT_OFF:
                    self._driver.set_command(command_code=dvr.COMMAND_LEFT,
                                             command_value=False)
                elif data_byte == Commands.RIGHT_ON:
                    self._driver.set_command(command_code=dvr.COMMAND_RIGHT,
                                             command_value=True)
                elif data_byte == Commands.RIGHT_OFF:
                    self._driver.set_command(command_code=dvr.COMMAND_RIGHT,
                                             command_value=False)
                elif data_byte == Commands.TURBO_ON:
                    self._driver.set_command(command_code=dvr.COMMAND_TURBO,
                                             command_value=True)
                elif data_byte == Commands.TURBO_OFF:
                    self._driver.set_command(command_code=dvr.COMMAND_TURBO,
                                             command_value=False)

        finally:
            self._server.close()

        _logger.debug('{} stopped'.format(self.__class__.__name__))
