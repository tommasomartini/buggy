import logging
import multiprocessing as mp
import signal

import robot.components.ultrasonic_sensors.hc_sr04 as hc_sr04
import robot.components.ultrasonic_sensors.playknowlogy as playknowlogy
import robot.sensor.ultrasonic as ultrasonic

_logger = logging.getLogger(__name__)

_ULTRASONIC_SENSOR_FRONT_TRIG_PIN = 11
_ULTRASONIC_SENSOR_FRONT_ECHO_PIN = 7
_ULTRASONIC_SENSOR_REAR_TRIG_PIN = 25
_ULTRASONIC_SENSOR_REAR_ECHO_PIN = 8


def _detect_obstacle(distance_sensor):
    """Cyclically reads from the distance sensor to trigger its callbacks.

    Function to be run in a dedicated process. Stops when a SIGTERM is captured.

    Args:
        distance_sensor (:obj:`UltrasonicSensor`): Ultrasonic distance sensor
            to read.
    """
    # Stop condition.
    stop = False

    def _stop(signum, frame):
        nonlocal stop
        _logger.debug('Process captured signal {}'.format(signum))
        stop = True

    signal.signal(signal.SIGTERM, _stop)
    while not stop:
        for _ in distance_sensor.read():
            if stop:
                break

    _logger.debug('{} stopped'.format(mp.current_process().name))


class ObstacleBreak:
    """Stops the motors if an obstacle is detected in the moving way.

    This class spawns two parallel processes to monitor the front and the rear
    distance sensors.
    """

    def __init__(self, driver, distance_m):
        if distance_m <= 0:
            raise ValueError('Distance must be positive. '
                             'Provided is {}'.format(distance_m))

        # Stops the forward motion if an obstacle is detected.
        front_event = driver.safety_stop_forward_event
        self._front_sensor = ultrasonic.UltrasonicSensor(
            trig_pin=_ULTRASONIC_SENSOR_FRONT_TRIG_PIN,
            echo_pin=_ULTRASONIC_SENSOR_FRONT_ECHO_PIN,
            pulse_s=hc_sr04.PULSE_s,
            measure_interval_s=hc_sr04.MEASURE_INTERVAL_s,
            distance_threshold_m=distance_m,
            when_in_range=lambda: front_event.set(),
            when_out_of_range=lambda: front_event.clear(),
            name='DistanceSensorFront',
        )

        # Stops the backward motion if an obstacle is detected.
        rear_event = driver.safety_stop_backward_event
        self._rear_sensor = ultrasonic.UltrasonicSensor(
            trig_pin=_ULTRASONIC_SENSOR_REAR_TRIG_PIN,
            echo_pin=_ULTRASONIC_SENSOR_REAR_ECHO_PIN,
            pulse_s=playknowlogy.PULSE_s,
            measure_interval_s=playknowlogy.MEASURE_INTERVAL_s,
            distance_threshold_m=distance_m,
            when_in_range=lambda: rear_event.set(),
            when_out_of_range=lambda: rear_event.clear(),
            name='DistanceSensorRear',
        )

        self._obstacle_detection_process_front = \
            mp.Process(target=_detect_obstacle,
                       args=(self._front_sensor,),
                       name='ObstacleDetectionFront',
                       daemon=True)

        self._obstacle_detection_process_rear = \
            mp.Process(target=_detect_obstacle,
                       args=(self._rear_sensor,),
                       name='ObstacleDetectionRear',
                       daemon=True)

    def run(self):
        try:
            self._obstacle_detection_process_front.start()
            self._obstacle_detection_process_rear.start()
        finally:
            self.close()

        _logger.debug('{} started'.format(self.__class__.__name__))

    def close(self):
        self._obstacle_detection_process_front.terminate()
        self._obstacle_detection_process_rear.terminate()

        self._obstacle_detection_process_front.join()
        self._obstacle_detection_process_rear.join()

        self._front_sensor.close()
        self._rear_sensor.close()

        _logger.debug('{} stopped'.format(self.__class__.__name__))
