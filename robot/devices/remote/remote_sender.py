import logging

from pynput import keyboard

import robot.devices.remote.common as common
import robot.network as network

_logger = logging.getLogger(__name__)


_instructions = """Press ESC to quit.
Use the arrow keys to move.
Hold shift for turbo.
Press 'q' to shut down the robot (but not the remote).
"""


class RemoteSender:
    """Remote controller on user's side.

    The remote sends raw signals: it is up to the receiver to interpret them.
    """

    def __init__(self):
        self._client = network.UDPClient(ip=network.RASPBERRYPI_HOSTNAME,
                                         port=network.PORT)
        _logger.debug('{} initialized'.format(self.__class__.__name__))

    def _on_press(self, key):
        data_byte = common.key_bindings.get(key, (None, None))[0]
        if data_byte is not None:
            self._client.send(data_byte)

    def _on_release(self, key):
        if key == keyboard.Key.esc:
            # Note that this will shut down the remote but not the robot!
            return False

        data_byte = common.key_bindings.get(key, (None, None))[1]
        if data_byte is not None:
            self._client.send(data_byte)

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
