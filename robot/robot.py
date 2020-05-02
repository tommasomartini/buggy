import logging

from gpiozero import Robot

import common.network as network


def _main():
    _logger.info('Start robot')

    server = network.UDPServer(ip=network.RASPBERRYPI_HOSTNAME,
                               port=network.PORT)

    robot = Robot(left=(7, 8), right=(9, 10))
    is_moving = False

    try:
        for data in server.receive():
            if data == 'f' and not is_moving:
                is_moving = True
                robot.forward()

            elif data == 'b' and not is_moving:
                is_moving = True
                robot.backward()

            elif data == 'l' and not is_moving:
                is_moving = True
                robot.left()

            elif data == 'r' and not is_moving:
                is_moving = True
                robot.right()

            elif data == 's':
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
