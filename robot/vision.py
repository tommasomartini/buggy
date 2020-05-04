import logging
import time

import cv2
import numpy as np

logging.basicConfig(level=logging.DEBUG)
_logger = logging.getLogger(__name__)

_CAMERA_ID = 1
_FPS_hz = 100
fx = 2
fy = 2


def _initialize_camera():
    cap = cv2.VideoCapture(_CAMERA_ID)
    if not cap.isOpened():
        raise RuntimeError('Cannot open camera {}'.format(_CAMERA_ID))

    _logger.debug('Camera {}: opened'.format(_CAMERA_ID))

    ret_fps = cap.set(cv2.CAP_PROP_FPS, _FPS_hz)
    if ret_fps is False:

        raise RuntimeError('Camera {}: failed to set '
                           'FPS to {} '.format(_CAMERA_ID, _FPS_hz))

    actual_fps = cap.get(cv2.CAP_PROP_FPS)
    if actual_fps != _FPS_hz:
        _logger.warning('Camera {}: tried to set FPS to {}, '
                        'but actual FPS is {}'
                        .format(_CAMERA_ID, _FPS_hz, actual_fps))
    else:
        _logger.debug('Camera {}: set FPS to {}'.format(_CAMERA_ID, _FPS_hz))

    return cap


cap = _initialize_camera()

times = []
while(True):
    # Capture frame-by-frame
    _ret, frame = cap.read()
    cap_time = time.time()

    image_height, image_width, num_channels = frame.shape
    new_shape = (int(image_width / fx), int(image_height / fy))
    resized_frame = cv2.resize(frame, new_shape)

    _ret, compressed_frame = cv2.imencode('.jpg', resized_frame)
    # print('Compressed frame shape: {}'.format(compressed_frame.shape))
    frame_bytes = compressed_frame.tobytes()
    # print('Frame is {} bytes'.format(len(frame_bytes)))

    bytes_string = np.fromstring(frame_bytes, np.uint8)
    decoded_frame = cv2.imdecode(bytes_string, cv2.IMREAD_COLOR)
    grayscale_frame = cv2.cvtColor(decoded_frame, cv2.COLOR_BGR2GRAY)

    end_time = time.time()
    times.append(end_time - cap_time)

    # Display the resulting frame
    cv2.imshow('frame', grayscale_frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

print(sum(times) / len(times))

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()
