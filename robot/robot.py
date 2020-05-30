import logging
import multiprocessing as mp

import robot.components.ultrasonic_sensors.hc_sr04 as hc_sr04
import robot.components.ultrasonic_sensors.playknowlogy as playknowlogy
import robot.motion.keyboard_driver as keyboard_driver
import robot.sensor.ultrasonic as ultrasonic

logging.basicConfig(level=logging.DEBUG,
                    style='{',
                    format='[{threadName}][{name}][{levelname}] {message}')
_logger = logging.getLogger(__name__)

_ULTRASONIC_SENSOR_FRONT_TRIG_PIN = 11
_ULTRASONIC_SENSOR_FRONT_ECHO_PIN = 7
_ULTRASONIC_SENSOR_REAR_TRIG_PIN = 25
_ULTRASONIC_SENSOR_REAR_ECHO_PIN = 8


def _start_front_distance_sensor(event):
    distance_threshold_m = 10e-2
    front_distance_sensor = ultrasonic.UltrasonicSensor(
        trig_pin=_ULTRASONIC_SENSOR_FRONT_TRIG_PIN,
        echo_pin=_ULTRASONIC_SENSOR_FRONT_ECHO_PIN,
        pulse_s=hc_sr04.PULSE_s,
        measure_interval_s=hc_sr04.MEASURE_INTERVAL_s,
        distance_threshold_m=distance_threshold_m,
        when_in_range=lambda: event.set(),
        when_out_of_range=lambda: event.clear(),
        name='Front',
    )
    while True:
        for _ in front_distance_sensor.read():
            pass


def _start_rear_distance_sensor(event):
    distance_threshold_m = 10e-2
    rear_distance_sensor = ultrasonic.UltrasonicSensor(
        trig_pin=_ULTRASONIC_SENSOR_REAR_TRIG_PIN,
        echo_pin=_ULTRASONIC_SENSOR_REAR_ECHO_PIN,
        pulse_s=playknowlogy.PULSE_s,
        measure_interval_s=playknowlogy.MEASURE_INTERVAL_s,
        distance_threshold_m=distance_threshold_m,
        when_in_range=lambda: event.set(),
        when_out_of_range=lambda: event.clear(),
        name='Rear',
    )
    while True:
        for _ in rear_distance_sensor.read():
            pass


def _main():
    driver = keyboard_driver.KeyboardDriver()

    try:
        front_safety_device_process = mp.Process(
            target=_start_front_distance_sensor,
            args=(driver.engage_safety_stop_event,),
            daemon=True)
        front_safety_device_process.start()

        rear_safety_device_process = mp.Process(
            target=_start_rear_distance_sensor,
            args=(driver.engage_safety_stop_event,),
            daemon=True)
        rear_safety_device_process.start()

        # The driver will take over the console and block, so we need to call
        # it last.
        driver.run()
    except KeyboardInterrupt:
        pass

    front_safety_device_process.terminate()
    rear_safety_device_process.terminate()

    print('Bye')


if __name__ == '__main__':
    _main()

