from abc import ABCMeta, abstractmethod
import time
import logging
from threading import Event


from smbus3 import SMBus
import gpiozero

touchscreen_models = dict()


class MetaTouchScreen(ABCMeta):

    """meta class  for touch screen to store class and their model in a dict"""

    def __init__(cls, name, bases, dict):
        """store the class and in a dict upon creation"""
        ABCMeta.__init__(cls, name, bases, dict)
        touchscreen_models[name] = cls


class BaseTouchScreen(object, metaclass=ABCMeta):

    """Base class for touch screen models
    abstraction to provide interface of any touchscreen class"""

    @abstractmethod
    def input(self, timeout: int):
        """ block until a tap is detected. unblock only if tap coordinates
        have moved or after a timeout.
        :timeout: if timeout is a positive number, it blocks at most timeout seconds
        and raises TouchEpaperException if no input detected
        :returns: X, Y, S coordinates of one touch

        """
        pass

    @abstractmethod
    def sleep(self):
        """enter sleep mode to reduce consumption
        will be woke up if ask for input or gesture

        """
        pass

    @abstractmethod
    def start(self):
        """ enter the normal mode

        """
        pass

    @abstractmethod
    def stop(self):
        """ enter sleep mode and close the ports

        """
        pass

    @abstractmethod
    def wait_for_gesture(self):
        pass

    @abstractmethod
    def __enter__(self):
        pass

    @abstractmethod
    def __exit__(self, ex_type, ex_value, ex_traceback):
        pass


class GT1151Mock(BaseTouchScreen, metaclass=MetaTouchScreen):

    """mock touch screen interface of gt1151 (2.13 inch epaper display).
    the touch are replaced with input of keyboard. There is no need of gpio"""

    def input(self):
        """ touch is replaced by input """
        x_str = input('x=')
        y_str = input('y=')
        s_str = input('s=')
        return int(x_str), int(y_str), int(s_str)

    def wait_for_gesture(self):
        """gesture is replaced by input enter"""
        input('press enter to sim a gesture:\n')

    def __enter__(self):
        self.start()
        return self

    def start(self):
        logging.info('mock reset GT')

    def stop(self):
        logging.info('mock close connection of GT and sleep')

    def __exit__(self, ex_type, ex_value, ex_traceback):
        self.stop()
        pass

    def sleep(self):
        logging.info('mock sleep of touchscreen')


class TouchEpaperException(Exception):
    pass


class GT1151(BaseTouchScreen, metaclass=MetaTouchScreen):

    """touch screen class for gt1151 (2.13 inch epaper display)"""

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
    _COMMAND = dict(
            sleep_mode=0x05,
            gesture_mode=0x08,
            )
    _GESTURE_TYPES = {
            0xaa: 'right_slide',
            0xbb: 'left_slide',
            0xab: 'slide_down',
            0xba: 'slide_up',
            0xcc: 'double_click',
            }

    def __init__(self):

        self._bus = SMBus(1)

        self._gpio_trst = gpiozero.LED(self._TRST)
        self._gpio_int = gpiozero.Button(self._INT, pull_up=False)

        self._x = [0] * 10
        self._y = [0] * 10
        self._s = [0] * 10
        self._gesture = None

        self._stopped = False
        self._started = False
        self._mode = None
        self._touch_detected = Event()
        self._gesture_detected = Event()

    def __enter__(self):
        self._enter_normal_mode()
        self._get_product_id()
        self._started = True
        return self

    def start(self):
        self._check_if_stopped()
        self._enter_normal_mode()
        self._get_product_id()
        self._started = True

    def __exit__(self, ex_type, ex_value, ex_traceback):
        if not self._stopped:
            self.stop()

    def _reset(self):
        self._gpio_int.when_pressed = lambda: None
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

    def _send_command(self, command, data):
        check_sum = 0x100 - command - data
        self._i2c_writebyte(
                self._REGISTER['command'],
                command,
                )
        self._i2c_writebyte(
                self._REGISTER['command_data'],
                data,
                )
        self._i2c_writebyte(
                self._REGISTER['command_checksum'],
                check_sum,
                )

    def _get_product_id(self):
        length = 4
        buf = self._i2c_readbyte(self._REGISTER['product_id'], length)
        product_id = ''.join(chr(el) for el in buf)
        logging.info('product id: %s', product_id)

    def _enter_normal_mode(self):
        logging.debug('enter normal mode')
        self._reset()
        self._gpio_int.when_pressed = self._process_coordinate_reading
        self._mode = 'normal'

    def _enter_sleep_mode(self):
        logging.debug('enter sleep mode')
        self._gpio_int.when_pressed = lambda: None
        self._send_command(
                self._COMMAND['sleep_mode'],
                0x00,
                )
        self._mode = 'sleep'

    def _enter_gesture_mode(self):
        logging.debug('enter gesture mode')
        self._gpio_int.when_pressed = self._process_gesture_reading
        self._send_command(
                self._COMMAND['gesture_mode'],
                0x00,
                )
        self._mode = 'gesture'

    def _process_gesture_reading(self):
        logging.debug('INT pressed!')
        buf = self._i2c_readbyte(
                self._REGISTER['gesture_type'],
                length=1,
                )
        gesture = buf[0]
        logging.debug('gesture is %s', self._GESTURE_TYPES.get(gesture))
        self._i2c_writebyte(
                self._REGISTER['gesture_type'],
                0x0,
                )
        if gesture:
            self._gesture = gesture
            self._gesture_detected.set()

    def sleep(self):
        self._check_if_started()
        self._check_if_stopped()
        if self._mode != 'sleep':
            self._enter_sleep_mode()

    def stop(self):
        self._check_if_stopped()

        self._reset()
        if self._mode != 'sleep':
            self._enter_sleep_mode()
        logging.debug('close connections to touch screen')
        self._bus.close()
        self._gpio_trst.off()
        self._gpio_trst.close()
        self._gpio_int.close()
        self._stopped = True

    def _answer_to_FW_request(self):

        logging.debug('there is a FW request')

        buf = self._i2c_readbyte(self._REGISTER['fw_request'], length=3)
        request = buf[0]
        FW_status_L = buf[1]
        FW_status_H = buf[2]
        FW_status = self._add_lo_hi_bytes(FW_status_L, FW_status_H)
        logging.debug('fw request %s', hex(request))
        logging.debug('fw status %s', FW_status)

        if request == 0x01:
            logging.debug(
                    'request for master to send configuration information')
            logging.debug('feature not implemented. I do nothing')
        elif request == 0x03:
            logging.debug('request master to reset.')
            self._enter_normal_mode()
        else:
            logging.debug('no need to process')
        self._i2c_writebyte(self._REGISTER['fw_request'], 0x0)

    def _read_coordinates(self, n_touch_points):

        logging.debug('read coordinates')
        buf = self._i2c_readbyte(
                self._REGISTER['coordinates_values'],
                length=n_touch_points*8)

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

            buf = self._i2c_readbyte(
                    self._REGISTER['coordinates_info'],
                    length=1)
            buffer_status = self._get_bits(buf[0], 7)
            n_touch_points = self._get_bits(buf[0], 0, 3)
            logging.debug('buffer status is %s', buffer_status)

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
                    self._touch_detected.set()
                self._i2c_writebyte(self._REGISTER['coordinates_info'], 0x0)

    def _check_if_stopped(self):
        if self._stopped:
            msg = 'touch screen has already been stopped.'
            logging.exception(msg)
            raise TouchEpaperException()

    def _check_if_started(self):
        if not self._started:
            msg = 'touch screen has not started.'
            logging.exception(msg)
            raise TouchEpaperException()

    def input(self):
        self._check_if_started()
        self._check_if_stopped()

        if not self._mode == 'normal':
            self._enter_normal_mode()

        old_coord = self._x[0], self._y[0], self._s[0]
        new_coord = self._x[0], self._y[0], self._s[0]
        self._touch_detected.clear()
        while new_coord == old_coord:
            self._touch_detected.wait()
            new_coord = self._x[0], self._y[0], self._s[0]
            self._touch_detected.clear()
        return new_coord

    def wait_for_gesture(self, gesture='left_slide'):
        """switch to gesture wake up mode and will return when gesture detected
        :gesture: one of
        (right_slide, left_slide, slide_up, slide_down, double_click,)

        """
        if gesture not in self._GESTURE_TYPES.values():
            msg = 'gesture type not implemented'
            logging.exception(msg)
            raise TouchEpaperException(msg)
        self._check_if_started()
        self._check_if_stopped()

        if self._mode != 'gesture':
            self._enter_gesture_mode()
        correct_gesture = False
        self._gesture_detected.clear()
        while not correct_gesture:
            self._gesture_detected.wait()
            correct_gesture = self._GESTURE_TYPES.get(self._gesture) == gesture
            self._gesture_detected.clear()


if __name__ == '__main__':
    gt1151 = GT1151()
