import logging

import robot.devices.led_status as ls
import robot.devices.line_navigator as ln
import robot.devices.obstacle_break as ob
import robot.devices.remote.remote_receiver as rr
import robot.motion.driver as dvr

_logger = logging.getLogger(__name__)


def _run_manual():
    driver = dvr.Driver()
    obstacle_break = ob.ObstacleBreak(driver=driver, distance_m=0.1)
    status_led = ls.StatusLed()
    remote_receiver = rr.RemoteReceiver(driver=driver, status_led=status_led)

    try:
        # Enable the automatic obstacle break.
        obstacle_break.run()

        # Start the receiver to drive the motors.
        remote_receiver.run()

    except KeyboardInterrupt:
        # Legit way to interrupt the application.
        pass

    finally:
        # However it goes, we want to perform these actions.
        status_led.close()
        obstacle_break.close()
        driver.close()

        print('Buggy correctly stopped.')


def _run_auto():
    driver = dvr.Driver()
    obstacle_break = ob.ObstacleBreak(driver=driver, distance_m=0.1)
    status_led = ls.StatusLed()

    line_navigator = ln.LineNavigator(driver=driver,
                                      status_led=status_led,
                                      black_track=True)

    try:
        obstacle_break.run()
        line_navigator.run()

    except KeyboardInterrupt:
        # Legit way to interrupt the application.
        pass

    finally:
        line_navigator.close()
        status_led.close()
        obstacle_break.close()
        driver.close()

        print('Buggy correctly stopped.')


def run(autopilot):
    if autopilot:
        _run_auto()
    else:
        _run_manual()
