import time
import logging


from waveshare_touch_epaper.touch_screen import GT1151


logging.basicConfig(level=logging.INFO)


def touch_screen():
    gt = GT1151()
    # print('normal test...')
    # gt = GT1151()
    # gt.start()
    # time.sleep(1)
    # gt.stop()

    # print('test with context manager')
    # with GT1151() as gt:
        # print('touch has started')
        # x, y, s = gt.input()
    # print(f'detected touch at {x}, {y},{s}')
    # print('touch should be closed')


if __name__ == '__main__':
    touch_screen()
