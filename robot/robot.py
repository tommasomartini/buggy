import logging

import robot.devices.obstacle_break as ob
import robot.devices.remote as remote
import robot.motion.driver as dvr

logging.basicConfig(level=logging.DEBUG,
                    style='{',
                    format='[{processName}][{name}][{levelname}] {message}')
_logger = logging.getLogger(__name__)


def _main():
    driver = dvr.Driver()
    obstacle_break = ob.ObstacleBreak(driver=driver, distance_m=0.1)
    remote_receiver = remote.RemoteReceiver(driver=driver)

    try:
        obstacle_break.run()
        remote_receiver.run()
    except KeyboardInterrupt:
        pass

    obstacle_break.close()
    driver.close()

    print('Buggy correctly stopped.')


if __name__ == '__main__':
    _main()

