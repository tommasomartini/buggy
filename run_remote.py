import logging

import robot.devices.remote.remote_sender as rs

logging.basicConfig(level=logging.DEBUG,
                    style='{',
                    format='[{processName}][{name}][{levelname}] {message}')


def _main():
    rs.RemoteSender().run()


if __name__ == '__main__':
    _main()
