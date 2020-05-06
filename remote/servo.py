import logging
import time

from pynput import keyboard

import common.network as network

_SEND_EVERY_s = 0
_L_KEY = keyboard.Key.left
_R_KEY = keyboard.Key.right

_STRING_ENCODING = 'utf-8'


def _main():
    _logger.info('Start remote')

    client = network.UDPClient(ip=network.RASPBERRYPI_HOSTNAME,
                               port=network.PORT)

    last_send_time = 0

    def _send_data(data_str):
        nonlocal last_send_time
        if time.time() - last_send_time > _SEND_EVERY_s:
            client.send(bytes(data_str, _STRING_ENCODING))
            last_send_time = time.time()

    def _on_press(key):
        if key == _L_KEY:
            data_str = 'l'
        elif key == _R_KEY:
            data_str = 'r'
        else:
            return

        _send_data(data_str)

    def _on_release(key):
        if key == keyboard.Key.esc:
            # Exit the program.
            return False

        if key in (_L_KEY, _R_KEY):
            _send_data('s')

    with keyboard.Listener(on_press=_on_press,
                           on_release=_on_release) as listener:
        listener.join()

    client.close()
    _logger.info('Stop remote')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    _logger = logging.getLogger(__name__)
    _main()
