import logging

from gpiozero import Robot

import common.network as network

_STRING_ENCODING = 'utf-8'


def _main():
    _logger.info('Start robot')

    server = network.UDPServer(ip=network.RASPBERRYPI_HOSTNAME,
                               port=network.PORT)

    robot = Robot(left=(7, 8), right=(9, 10))
    is_moving = False

    try:
        for data in server.receive():
            data_str = data.decode(_STRING_ENCODING)
            if data_str == 'f' and not is_moving:
                is_moving = True
                robot.forward()

            elif data_str == 'b' and not is_moving:
                is_moving = True
                robot.backward()

            elif data_str == 'l' and not is_moving:
                is_moving = True
                robot.left()

            elif data_str == 'r' and not is_moving:
                is_moving = True
                robot.right()

            elif data_str == 's':
                is_moving = False
                robot.stop()

    except KeyboardInterrupt:
        pass

    finally:
        robot.stop()
        server.close()
        _logger.info('Stop robot')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    _logger = logging.getLogger(__name__)
    _main()
