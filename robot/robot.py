import logging

import robot.devices.led_status as ls
import robot.devices.obstacle_break as ob
import robot.devices.remote.remote_receiver as rr
import robot.motion.driver as dvr

_logger = logging.getLogger(__name__)


def run():
    driver = dvr.Driver()
    obstacle_break = ob.ObstacleBreak(driver=driver, distance_m=0.1)
    status_led = ls.StatusLed()
    remote_receiver = rr.RemoteReceiver(driver=driver,
                                        status_led=status_led)

    try:
        obstacle_break.run()
        remote_receiver.run()
    except KeyboardInterrupt:
        pass

    remote_receiver.close()
    obstacle_break.close()
    status_led.close()
    driver.close()

    print('Buggy correctly stopped.')
