import logging

from pynput import keyboard

import common.network as network

_FW_KEY = keyboard.Key.up
_BW_KEY = keyboard.Key.down
_L_KEY = keyboard.Key.left
_R_KEY = keyboard.Key.right

_STRING_ENCODING = 'utf-8'


def _main():
    _logger.info('Start remote')

    client = network.UDPClient(ip=network.RASPBERRYPI_HOSTNAME,
                               port=network.PORT)

    def _on_press(key):
        if key == _FW_KEY:
            data_str = 'f'
        elif key == _BW_KEY:
            data_str = 'b'
        elif key == _L_KEY:
            data_str = 'l'
        elif key == _R_KEY:
            data_str = 'r'
        else:
            return

        client.send(bytes(data_str, _STRING_ENCODING))

    def _on_release(key):
        if key == keyboard.Key.esc:
            return False

        if key in (_FW_KEY, _BW_KEY, _L_KEY, _R_KEY):
            # Send a stop signal.
            data_str = 's'
            client.send(bytes(data_str, _STRING_ENCODING))

    with keyboard.Listener(on_press=_on_press,
                           on_release=_on_release) as listener:
        listener.join()

    client.close()
    _logger.info('Stop remote')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    _logger = logging.getLogger(__name__)
    _main()
