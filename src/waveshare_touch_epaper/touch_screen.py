import time
import threading
import logging


from smbus3 import SMBus
import gpiozero


class TouchEpaperException(Exception):
    pass


class GT1151(object):

    """touch screen part of the 2.13 inch touch epaper display"""

    _TRST = 22
    _INT = 27
    _ADDRESS = 0x14

    def __init__(self):

        self._bus = SMBus(1)

        self._gpio_trst = gpiozero.LED(self._TRST)
        self._gpio_int = gpiozero.Button(self._INT, pull_up=False)
        self._int_value = 0

        self._x = [0] * 5
        self._y = [0] * 5
        self._s = [0] * 5
        self._x_old = [0] * 5
        self._y_old = [0] * 5
        self._s_old = [0] * 5

        self._touch_detected = False

        self._flag_t = 1

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
            if self._gpio_int.value == 0:
                self._int_value = 1
            else:
                self._int_value = 0
        logging.info("thread:exit")

    def _reset(self):
        self._gpio_trst.on()
        time.sleep(0.1)
        self._gpio_trst.off()
        time.sleep(0.1)
        self._gpio_trst.on()
        time.sleep(0.1)

    def _i2c_writebyte(self, reg, value):
        self._bus.write_word_data(
                self._ADDRESS,
                (reg >> 8) & 0xff,
                (reg & 0xff) | ((value & 0xff) << 8),
                )

    def _i2c_write(self, reg):
        self._bus.write_byte_data(
                self._ADDRESS,
                (reg >> 8) & 0xff,
                reg & 0xff,
                )

    def _get_bits(self, value, first_bit, last_bit=None):
        if last_bit is None:
            last_bit = first_bit
            shift = first_bit
            nbits = last_bit - first_bit + 1
            mask = 2 ** nbits - 1
            bits = (value >> shift) & mask
            return bits

    def _i2c_readbyte(self, reg, length):
        self._i2c_write(reg)
        rbuf = []
        for i in range(length):
            rbuf.append(int(self._bus.read_byte(self._ADDRESS)))
        return rbuf

    def _add_lo_hi_bytes(self, low_byte, high_byte):
        new_byte = (high_byte << len(low_byte)) + low_byte
        return new_byte

    def _get_product_id(self):
        address = 0x8140
        length = 4
        buf = self._i2c_readbyte(address, length)
        logging.info('product id: %s', buf)

    def _gt_init(self):
        self._reset()
        self._get_product_id()

    def start(self):
        """start the thread and init the touch device

        """
        if not self._stopped:
            self._thread_gt.start()
            logging.info("init touch screen")
            self._gt_init()
            self._ready = True
        else:
            logging.exception(
                    'touch screen has previousely been stopped.',
                    'you must recreate and instance of GT1151 and start it.')
            raise TouchEpaperException()

    def stop(self):
        """close the ports and finish thread
        :returns: TODO

        """

        if not self._stopped and self._ready:
            self._flag_t = 0
            self._thread_gt.join()
            logging.info('close connection to touch screen')
            self._bus.close()
            self._gpio_trst.off()
            self._gpio_trst.close()
            self._gpio_int.close()
            self._stopped = True
        else:
            msg = 'touch screen has already been stopped or not yet started.'
            logging.exception(msg)
            raise TouchEpaperException()

    def _scan(self):
        """
        scan and assign touch coordinates (up to 5 points)
        to _x _y and _s attributes
        """
        buf = []
        mask = 0x00

        if self._int_value == 1:
            self._int_value = 0

            # read coordinate informations
            buf = self._i2c_readbyte(reg=0x814E, length=1)
            buffer_status = self._get_bits(buf[0], 7)

            if buffer_status == 0:  # device note ready and data invalid
                time.sleep(0.01)
            else:  # coordinates ready to be read
                n_touch_points = self._get_bits(buf[0], 0, 3)
                logging.debug('detected %s touch', n_touch_points)

                if n_touch_points > 0:

                    # read coordinates
                    buf = self._i2c_readbyte(reg=0x814F, length=n_touch_points*8)

                    self._x_old[0] = self._x[0]
                    self._y_old[0] = self._y[0]
                    self._s_old[0] = self._s[0]

                    for i in range(n_touch_points):
                        low_byte_x = buf[1+8*i]
                        high_byte_x = buf[2+8*i]
                        low_byte_y = buf[3+8*i]
                        high_byte_y = buf[4+8*i]
                        low_byte_s = buf[5+8*i]
                        high_byte_s = buf[6+8*i]
                        self._x[i] = self._add_lo_hi_bytes(low_byte_x, high_byte_x)
                        self._y[i] = self._add_lo_hi_bytes(low_byte_y, high_byte_y)
                        self._s[i] = self._add_lo_hi_bytes(low_byte_s, high_byte_s)

                    self._touch_detected = True

                    logging.debug(
                            'dev pos=%s %s %s',
                            self._x[0],
                            self._y[0],
                            self._s[0],
                            )
                else:
                    logging.debug('wrong number of touch detected')
            # must write 0 after coordinate read
            self._i2c_writebyte(reg=0x814E, value=mask)

    def input(self):
        """scan until a touch has been detected at a new position
        :returns: X, Y, S coordinates of one touch

        """
        if not self._stopped and self._ready:
            new_position = False
            while not new_position:
                self._scan()
                if self._touch_detected:
                    if not (
                            self._x == self._x_old
                            and self._y == self._y_old
                            ):
                        new_position = True
                    self._touch_detected = False
            return self._x[0], self._y[0], self._y[0]
        else:
            msg = 'touch screen has already been stopped or not yet started.'
            logging.exception(msg)
            raise TouchEpaperException()


if __name__ == '__main__':
    gt1151 = GT1151()
