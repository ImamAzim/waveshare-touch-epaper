import threading
import logging


from smbus3 import SMBus
import gpiozero


address = 0x1


class TouchEpaperException(Exception):
    pass


class GT1151(object):

    """touch screen part of the 2.13 inch touch epaper display"""

    def __init__(self):

        # gt1151.config.bus = SMBus(1)
        # gt1151.config.GPIO_TRST = gpiozero.LED(gt1151.config.TRST)
        # gt1151.config.GPIO_INT = gpiozero.Button(gt1151.config.INT, pull_up = False)

        self._flag_t = 1

        self._gt = gt1151.GT1151()
        self._gt_dev = gt1151.GT_Development()
        self._gt_old = gt1151.GT_Development()

        self._thread_gt = threading.Thread(target=self._pthread_irq)
        self._thread_gt.setDaemon(True)

        self._ready = False
        self._stopped = False

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, ex_type, ex_value, ex_traceback):
        if not self._stopped:
            self.stop()

    def _pthread_irq(self):
        logging.info("pthread running")
        while self._flag_t == 1:
            if self._gt.digital_read(self._gt.INT) == 0:
                self._gt_dev.Touch = 1
                # logging.debug('switch dev.touch to 1')
            else:
                self._gt_dev.Touch = 0
                # logging.debug('switch dev.touch to 0')
        logging.info("thread:exit")

    def start(self):
        """start the thread and init the touch device

        """
        if not self._stopped:
            self._thread_gt.start()
            logging.info("init touch screen")
            self._gt.GT_Init()
            self._ready = True
        else:
            logging.exception(
                    'touch screen has been stopped.',
                    'you must recreate and instance of EGT1151 and start it.')
            raise TouchEpaperException()

    def stop(self):
        """close the port for the touch and finish thread
        :returns: TODO

        """

        if not self._stopped and self._ready:
            self._flag_t = 0
            self._thread_gt.join()
            logging.info('close connection to touch screen')
            gt1151.config.bus.close()
            gt1151.config.GPIO_TRST.off()
            gt1151.config.GPIO_TRST.close()
            gt1151.config.GPIO_INT.close()
            self._stopped = True
        else:
            msg = 'touch screen has already been stopped or not yet started.'
            logging.exception(msg)
            raise TouchEpaperException()

    def input(self):
        """scan until a touch has been detected at a new position
        :returns: X, Y, S coordinates of touch

        """
        if not self._stopped and self._ready:
            new_position = False
            logging.debug('gt_dev.touch=%s', self._gt_dev.Touch)
            logging.debug(
                    'old pos=%s %s %s, dev pos=%s %s %s',
                    self._gt_old.X[0],
                    self._gt_old.Y[0],
                    self._gt_old.S[0],
                    self._gt_dev.X[0],
                    self._gt_dev.Y[0],
                    self._gt_dev.S[0],
                    )

            while not new_position:
                self._gt.GT_Scan(self._gt_dev, self._gt_old)
                if self._gt_dev.TouchpointFlag:
                    if not (
                            self._gt_dev.X == self._gt_old.X
                            and self._gt_dev.Y == self._gt_old.Y
                            ):
                        new_position = True
            self._gt_dev.TouchpointFlag = 0
            return self._gt_dev.X[0], self._gt_dev.Y[0], self._gt_dev.S[0]
        else:
            msg = 'touch screen has already been stopped or not yet started.'
            logging.exception(msg)
            raise TouchEpaperException()


if __name__ == '__main__':
    pass
