import time
import threading
import logging


from smbus3 import SMBus
import gpiozero


class TouchEpaperException(Exception):
    pass


class GT_Development:
    """ internal class to keep track of touchscreen state """
    def __init__(self):
        self.Touch = 0
        self.TouchpointFlag = 0
        self.TouchCount = 0
        self.Touchkeytrackid = [0, 1, 2, 3, 4]
        self.X = [0, 1, 2, 3, 4]
        self.Y = [0, 1, 2, 3, 4]
        self.S = [0, 1, 2, 3, 4]


class GT1151(object):

    """touch screen part of the 2.13 inch touch epaper display"""

    _TRST = 22
    _INT = 27
    _ADDRESS = 0x14

    def __init__(self):

        self._bus = SMBus(1)

        self._gpio_trst = gpiozero.LED(self._TRST)
        self._gpio_int = gpiozero.Button(self._INT, pull_up = False)

        self._flag_t = 1

        self._gt_dev = GT_Development()
        self._gt_old = GT_Development()

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

    # def _digital_read(self):
            # return self._gpio_int.value

    def _pthread_irq(self):
        logging.info("pthread running")
        while self._flag_t == 1:
            if self._gpio_int.value == 0:
                self._gt_dev.Touch = 1
            else:
                self._gt_dev.Touch = 0
        logging.info("thread:exit")

    # def _digital_write(self, value):
        # if value:
            # self._gpio_trst.on()
        # else:
            # self._gpio_trst.off()

    def _reset(self):
        self._gpio_trst.on()
        time.sleep(0.1)
        self._gpio_trst.off()
        time.sleep(0.1)
        self._gpio_trst.on()
        time.sleep(0.1)

    def _i2c_write(self, reg):
        self._bus.write_byte_data(self._ADDRESS, (reg>>8) & 0xff, reg & 0xff)

    def i2c_readbyte(reg, len):
        i2c_write(reg)
        rbuf = []
        for i in range(len):
            rbuf.append(int(bus.read_byte(address)))
        return rbuf

    def GT_Read(self, Reg, len):
        return config.i2c_readbyte(Reg, len)

    def GT_ReadVersion(self):
        buf = self.GT_Read(0x8140, 4)
        print(buf)

    def GT_Init(self):
        self.GT_Reset()
        self.GT_ReadVersion()

    def start(self):
        """start the thread and init the touch device

        """
        if not self._stopped:
            self._thread_gt.start()
            logging.info("init touch screen")
            self._GT_Init()
            self._ready = True
        else:
            logging.exception(
                    'touch screen has been stopped.',
                    'you must recreate and instance of GT1151 and start it.')
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
    gt1151 = GT1151()
    pass
