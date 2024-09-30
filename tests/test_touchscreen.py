import unittest
import time
import logging


from waveshare_touch_epaper.touch_screen import GT1151
from waveshare_touch_epaper import touchscreen_models


logging.basicConfig(level=logging.INFO)


class TestTouchMock(unittest.TestCase):

    def test_mock_interface(self):
        gt = touchscreen_models['GT1151Mock']()


def touch_screen():

    with GT1151() as gt:
        print('please touch the screen')
        x, y, s = gt.input()
        print(f'detected touch at {x}, {y}')
        x, y, s = gt.input()
        print('please touch the screen a 2nd time')
        print(f'detected touch at {x}, {y}')
        print('please do a left slide')
        gt.wait_for_gesture()
        print('success')


if __name__ == '__main__':
    touch_screen()
