import logging

import robot.devices.obstacle_break as ob
import robot.motion.keyboard_driver as keyboard_driver

logging.basicConfig(level=logging.DEBUG,
                    style='{',
                    format='[{processName}][{name}][{levelname}] {message}')
_logger = logging.getLogger(__name__)


def _main():
    driver = keyboard_driver.KeyboardDriver()
    obstacle_break = ob.ObstacleBreak(driver=driver, distance_m=0.1)

    try:
        obstacle_break.run()

        # The driver will block: call it last.
        driver.run()
    except KeyboardInterrupt:
        pass

    obstacle_break.close()

    print('Bye')


if __name__ == '__main__':
    _main()

