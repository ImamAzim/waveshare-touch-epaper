import time
import logging


from waveshare_touch_epaper.touch_screen import GT1151


logging.basicConfig(level=logging.DEBUG)


def touch_screen():

    print('test with context manager')
    with GT1151() as gt:
        x, y = gt.input()
    print(f'detected touch at {x}, {y}')


if __name__ == '__main__':
    touch_screen()
