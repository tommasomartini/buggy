import logging

import robot.motion.keyboard_driver as keyboard_driver

logging.basicConfig(level=logging.DEBUG,
                    style='{',
                    format='[{threadName}][{name}][{levelname}] {message}')


def _main():
    keyboard_driver.KeyboardDriver()


if __name__ == '__main__':
    _main()

