import logging
import time

from pynput import mouse

import common.network as network
import signal

_SEND_EVERY_s = 0

_STRING_ENCODING = 'utf-8'


dx = 0
dy = 0
pos_x = 0
pos_y = 0
last_time = time.time()


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

    def _on_move(x, y):
        global dx
        global dy
        global pos_x
        global pos_y
        global last_time

        now = time.time()
        dt = now - last_time

        if x == pos_x:
            # Motion detected, but the position did not change: it means that
            # we are pushing against one the screen's border.
            # Keep the last velocity.
            pass
        else:
            dx = (x - pos_x) / dt
            dy = (y - pos_y) / dt
            pos_x = x
            pos_y = y

        last_time = now

        print('dx={: 8.1f} dy={: 8.1f}'.format(dx, dy))

        if abs(dx) < 300:
            _send_data('s')
        elif dx > 0:
            _send_data('r')
        elif dx < 0:
            _send_data('l')

        signal.setitimer(signal.ITIMER_REAL, 0.1, 0)

    def _on_click(x, y, button, pressed):
        if button == mouse.Button.right:
            # Stop listener
            return False

    def _on_stop(signum, frame):
        _send_data('s')

    signal.signal(signal.SIGALRM, _on_stop)

    with mouse.Listener(on_click=_on_click,
                        on_move=_on_move,
                        suppress=True) as l:
        l.join()

    client.close()
    _logger.info('Stop remote')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    _logger = logging.getLogger(__name__)
    _main()
