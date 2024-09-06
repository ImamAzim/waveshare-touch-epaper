import time
import logging
from threading import RLock


from smbus3 import SMBus
import gpiozero


class TouchEpaperException(Exception):
    pass


class GT1151(object):

    """touch screen part of the 2.13 inch touch epaper display"""

    _TRST = 22
    _INT = 27
    _ADDRESS = 0x14
    _REGISTER = dict(
            command=0x8040,
            command_data=0x8041,
            command_checksum=0x8042,
            fw_request=0x8044,
            coordinates_info=0x814E,
            coordinates_values=0x814F,
            product_id=0x8140,
            gesture_type=0x814C,
            )

    def __init__(self):

        self._bus = SMBus(1)

        self._gpio_trst = gpiozero.LED(self._TRST)
        self._gpio_int = gpiozero.Button(self._INT, pull_up=False)

        self._x = [0] * 10
        self._y = [0] * 10
        self._s = [0] * 10
        self._x_old = [0] * 10
        self._y_old = [0] * 10
        self._s_old = [0] * 10

        self._stopped = False
        self._coordinates_lock = RLock()

    def __enter__(self):
        self._enter_normal_mode()
        self._get_product_id()
        return self

    def start(self):
        """ enter the normal mode

        """
        self._enter_normal_mode()
        self._get_product_id()

    def __exit__(self, ex_type, ex_value, ex_traceback):
        if not self._stopped:
            self.stop()

    def _reset(self):
        self._gpio_int.when_pressed = None
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

    def _add_lo_hi_bytes(self, low_byte, high_byte, nbits=8):
        new_byte = (high_byte << nbits) + low_byte
        return new_byte

    def _get_product_id(self):
        length = 4
        buf = self._i2c_readbyte(self._REGISTER['product_id'], length)
        product_id = ''.join(chr(el) for el in buf)
        logging.info('product id: %s', product_id)

    def _enter_normal_mode(self):
        logging.debug('enter normal mode')
        self._reset()
        self._gpio_int.when_pressed = self._process_coordinate_reading

    def stop(self):
        """ enter sleep mode and close the ports

        """

        if not self._stopped:
            self._reset()
            logging.debug('TODO: enter sleep mode')
            logging.info('close connections to touch screen')
            self._bus.close()
            self._gpio_trst.off()
            self._gpio_trst.close()
            self._gpio_int.close()
            self._stopped = True
        else:
            msg = 'touch screen has already been stopped'
            logging.exception(msg)
            raise TouchEpaperException()

    def _answer_to_FW_request(self):

        logging.debug('there is a FW request')

        buf = self._i2c_readbyte(self._REGISTER['fw_request'], length=1)
        request = buf[0]

        if request == 0x01:
            logging.debug(
                    'request for master to send configuration information')
            logging.debug('feature not implemented. I do nothing')
        elif request == 0x03:
            logging.debug('request master to reset.')
            logging.debug('i enter normal mode, assuming I was there')
            self._enter_normal_mode()
        else:
            logging.debug('no need to process')

    def _has_touch_moved(self):
        with self._coordinates_lock:
            if (
                    self._x_old[0] == self._x[0] and
                    self._y_old[0] == self._y[0] and
                    ):
                return False
            else:
                return True

    def _read_coordinates(self, n_touch_points):

        logging.debug('read coordinates')
        buf = self._i2c_readbyte(
                self._REGISTER['coordinates_values'],
                length=n_touch_points*8)

        with self._coordinates_lock:
            # store old values
            self._x_old[0] = self._x[0]
            self._y_old[0] = self._y[0]
            self._s_old[0] = self._s[0]

            # get new coord and assign
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

        logging.debug(
                'new coordinates=%s %s %s',
                self._x[0],
                self._y[0],
                self._s[0],
                )
        # must write 0 after coordinate read
        logging.debug('write 0 to register because coordinate read')
        self._i2c_writebyte(self._REGISTER['coordinates_info'], 0x0)

    def _process_coordinate_reading(self, triggered=True):
        """
        follow the process of coordinate reading
        :triggered: True if triggered by int, false if polling
        """
        if triggered:
            logging.debug('INT has been pressed!')
        else:
            logging.debug('polling..')

        last_iteration = False
        while last_iteration is not True:
            last_iteration = True

            logging.debug('check buffer status')
            buf = self._i2c_readbyte(
                    self._REGISTER['coordinates_info'],
                    length=1)
            buffer_status = self._get_bits(buf[0], 7)
            n_touch_points = self._get_bits(buf[0], 0, 3)

            if buffer_status == 0:  # device note ready and data invalid
                if triggered:
                    self._answer_to_FW_request()
                else:
                    logging.debug('device not ready, wait 10ms')
                    time.sleep(0.01)
                    last_iteration = False
            else:
                logging.debug('detected %s touch', n_touch_points)
                if n_touch_points > 0:
                    self._read_coordinates(n_touch_points)

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
