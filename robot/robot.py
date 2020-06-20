import logging

import robot.devices.obstacle_break as ob
import robot.devices.remote.remote_receiver as rr
import robot.motion.driver as dvr

_logger = logging.getLogger(__name__)


def run():
    driver = dvr.Driver()
    obstacle_break = ob.ObstacleBreak(driver=driver, distance_m=0.1)
    remote_receiver = rr.RemoteReceiver(driver=driver)

    try:
        obstacle_break.run()
        remote_receiver.run()
    except KeyboardInterrupt:
        pass

    obstacle_break.close()
    driver.close()

    print('Buggy correctly stopped.')
