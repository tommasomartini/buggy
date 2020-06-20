import argparse
import logging

import robot.robot

logging.basicConfig(level=logging.DEBUG,
                    style='{',
                    format='[{processName}][{name}][{levelname}] {message}')


def _main():
    parser = argparse.ArgumentParser(
        description='Start the robot or the remote controlling it.')
    parser.add_argument('-a',
                        '--auto',
                        action='store_true',
                        help='If set, starts the robot in line-tracking mode.')
    args = parser.parse_args()

    if args.auto:
        robot.robot.run(autopilot=True)

    else:
        robot.robot.run(autopilot=False)


if __name__ == '__main__':
    _main()
