import time
from abc import ABCMeta, abstractmethod
import logging


import spidev
import gpiozero
from PIL import Image


epaper_models = dict()


class MetaEpaper(ABCMeta):

    """meta class  for epaper displays to store class
    and their model in a dict"""

    def __init__(cls, name, bases, dict):
        """store the class and in a dict upon creation"""
        ABCMeta.__init__(cls, name, bases, dict)
        epaper_models[name] = cls


class BaseEpaper(object, metaclass=ABCMeta):

    """Base class for epaper, define interface with abstract methid. """

    WIDTH: int = NotImplemented
    """width of screen in number of pixels"""

    HEIGHT: int = NotImplemented
    """height of screen in number of pixels"""

    @abstractmethod
    def open(self):
        """open the spi and gpio port

        """
        pass

    @abstractmethod
    def __enter__(self):
        """open port and full update
        :returns: self

        """
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_value, traceback):
        """exit the context manager. enter sleep mode and close all ports

        :exc_type: None if exited without exception
        :exc_value: None if exited without exception
        :traceback: None if exited without exception

        """
        pass

    @abstractmethod
    def close(self):
        """close the port so that display consume 0V

        """
        pass

    @abstractmethod
    def full_update(self):
        """initialization. should be called when the screen start working,
        after exiting sleep mode or possibly before full refresh

        """
        pass

    @abstractmethod
    def display(self, img: Image.Image, full: bool, wait: bool):
        """send img to epaper RAM and do a full or partial refresh
        (partial update will be called if full refresh)

        :img: that will be displayed
        :full: if True, apply a full refresh, otherise a partial one
        :wait: if True will wait for busy PIN(?)
        :raise EpaperException: when img has incorrect dimension

        """
        pass

    @abstractmethod
    def clear(self):
        """clear the e-paper to white

        """
        pass

    @abstractmethod
    def sleep(self):
        """enter deep sleep mode

        """
        pass


class EPD2in13Mock(BaseEpaper, metaclass=MetaEpaper):
    """mock interface for epaper display, 2.13 inch. no need of gpio,
    the image are displayed on the screen with pillow module"""

    WIDTH = 122
    HEIGHT = 250

    def full_update(self):
        logging.info('full update mock')

    def _partial_update(self):
        logging.info('partial update mock')

    def clear(self):
        img = Image.new('1', (self.WIDTH, self.HEIGHT), 255)
        img.show()

    def open(self):
        logging.info('mock open port epd')

    def close(self):
        logging.info('mock close port epd')

    def sleep(self):
        logging.info('mock: enter sleep mode')

    def display(self, img: Image.Image, full=True, wait=False):
        img.show()
        if full:
            self._partial_update()

    def __enter__(self):
        self.open()
        self.full_update()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.sleep()
        self.close()


class EpaperException(Exception):
    pass


class EPD2in13(BaseEpaper, metaclass=MetaEpaper):

    WIDTH = 122
    HEIGHT = 250
    _MAX_PARTIAL_REFRESH = 50

    _RST_PIN = 17
    _DC_PIN = 25
    _CS_PIN = 8
    _BUSY_PIN = 24

    _ADRESS = 0x14

    _SPI_MAXSPEED = 10000000
    _SPI_MODE = 0b00

    _COMMAND = dict(
            reset=0x12,
            driver_output_control=0x01,
            data_entry_mode_setting=0x11,
            set_ram_x=0x44,
            set_ram_y=0x45,
            border_waveform_control=0x3c,
            temperature_sensor_control=0x18,
            deep_sleep_mode=0x10,
            )

    def __init__(self):
        """initialise epd

        """
        self._remaining_partial_refresh = None

    def __enter__(self):
        self.open()
        return self

    def open(self):
        self._power_on()
        self._set_initial_configuration()
        self._send_initialization_code()
        self._load_waveform_lut()

    def close(self):
        self._power_off()

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def _power_on(self):
        logging.info('power on')
        # TODO: check VCI pin
        self._gpio_rst = gpiozero.LED(self._RST_PIN)
        self._gpio_dc = gpiozero.LED(self._DC_PIN)
        self._gpio_busy = gpiozero.Button(
                self._BUSY_PIN,
                pull_up=False)
        time.sleep(0.01)

    def _set_initial_configuration(self):
        logging.info('set initial configuration')
        self._spi = spidev.SpiDev(0, 0)
        self._spi.max_speed_hz = self._SPI_MAXSPEED
        self._spi.mode = self._SPI_MODE
        self._hw_reset()
        self._send_command('reset')
        time.sleep(0.01)

    def _send_initialization_code(self):
        logging.info('send initialization code')
        self._set_gate_driver_output()
        self._set_display_RAM_size(0, self.WIDTH-1, 0, self.HEIGHT-1)
        self._set_panel_border()

    def _load_waveform_lut(self):
        self._sense_temperature()
        self._wait_busy_low()

    def _power_off(self):
        logging.info('power off')
        self._deep_sleep()
        self._spi.close()
        # TODO: check VCI pin
        self._gpio_rst.off()
        self._gpio_dc.off()
        self._gpio_rst.close()
        self._gpio_dc.close()
        self._gpio_busy.close()

    def _hw_reset(self):
        self._gpio_rst.on()
        time.sleep(0.02)
        self._gpio_rst.off()
        time.sleep(0.002)
        self._gpio_rst.on()
        time.sleep(0.02)

    def _set_gate_driver_output(self):
        self._send_command('driver_output_control')
        self._send_data(0xf9)
        self._send_data(0x00)
        self._send_data(0x00)

    def _set_display_RAM_size(self, x_start, x_end, y_start, y_end):
        self._send_command('data_entry_mode_setting')
        self._send_data(0b011)
        self._send_command('set_ram_x')
        # coord are divided by 8 for RAM?
        self._send_data(x_start >> 3)
        self._send_data(x_end >> 3)
        self._send_command('set_ram_y')
        data = y_start
        low_byte, hi_byte = self._split_low_hi_bytes(data)
        self._send_data(low_byte)
        self._send_data(hi_byte)
        data = y_end
        low_byte, hi_byte = self._split_low_hi_bytes(data)
        self._send_data(low_byte)
        self._send_data(hi_byte)

    def _set_panel_border(self):
        self._send_command('border_waveform_control')
        vbd_opt = 0b00 << 6
        vbd_level = 0b00 << 4
        gs_control = 0b1 << 2  # follow LUT
        gs_setting = 0b01  # LUT1
        data = gs_control + gs_setting + vbd_level + vbd_opt
        self._send_data(data)

    def _sense_temperature(self):
        self._send_command('temperature_sense_control')
        self._send_data(0x80)

    def _wait_busy_low(self):
        self._gpio_busy.wait_for_press()

    def _deep_sleep(self):
        self._send_command('deep_sleep_mode')

    def _split_low_hi_bytes(large_byte):
        low_byte = large_byte & 0xff
        hi_byte = large_byte >> 8
        return low_byte, hi_byte

    def _send_command(self, cmd_key: str):
        command = self._COMMAND.get(cmd_key)
        self._gpio_dc.off()
        self._spi.writebytes([command])

    def _send_data(self, data):
        self._gpio_dc.on()
        self._spi.writebytes([data])

    def _partial_update(self):
        logging.info('partial update mock')

    def clear(self):
        img = Image.new('1', (self.WIDTH, self.HEIGHT), 255)
        img.show()

    def display(self, img: Image.Image, full=True, wait=False):
        if full:
            pass
            self._remaining_partial_refresh = self._MAX_PARTIAL_REFRESH
            self._partial_update()
        else:
            if self._remaining_partial_refresh == 0:
                msg = 'too many partial refresh. need a full refresh'
                raise EpaperException(msg)
            self._remaining_partial_refresh -= 1
