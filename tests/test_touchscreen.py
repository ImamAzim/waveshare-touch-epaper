import time
import logging


from waveshare_touch_epaper.touch_screen import GT1151


logging.basicConfig(level=logging.INFO)


def touch_screen():

    with GT1151() as gt:
        print('please touch the screen')
        x, y = gt.input()
        print(f'detected touch at {x}, {y}')
        x, y = gt.input()
        print('please touch the screen a 2nd time')
        print(f'detected touch at {x}, {y}')
        print('please slide up')
        gt.wait_for_gesture()
        print('success')


if __name__ == '__main__':
    touch_screen()
