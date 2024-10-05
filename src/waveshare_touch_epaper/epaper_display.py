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

    WIDTH = 250
    HEIGHT = 122

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

    WIDTH = 250
    HEIGHT = 122
    _MAX_PARTIAL_REFRESH = 50

    _RST_PIN = 17
    _DC_PIN = 25
    _CS_PIN = 8
    _BUSY_PIN = 24

    _ADRESS = 0x14

    _SPI_MAXSPEED = 10000000
    _SPI_MODE = 0b00

    def __init__(self):
        """initialise epd

        """
        self._remaining_partial_refresh = None

    def __enter__(self):
        self.open()
        self.full_update()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.sleep()
        self.close()

    def open(self):
        self._spi = spidev.SpiDev(0, 0)
        self._gpio_rst = gpiozero.LED(self._RST_PIN)
        self._gpio_dc = gpiozero.LED(self._DC_PIN)
        self._gpio_busy = gpiozero.Button(
                self._BUSY_PIN,
                pull_up=False)

        self._spi.max_speed_hz = self._SPI_MAXSPEED
        self._spi.mode = self._SPI_MODE

    def close(self):
        logging.info('close port epd')
        self._spi.close()
        self._gpio_rst.off()
        self._gpio_dc.off()
        self._gpio_rst.close()
        self._gpio_dc.close()
        self._gpio_busy.close()

    def full_update(self):
        logging.info('epd full update')
        self._hw_reset()

    def _hw_reset(self):
        self._gpio_rst.on()
        time.sleep(0.02)
        self._gpio_rst.off()
        time.sleep(0.002)
        self._gpio_rst.on()
        time.sleep(0.02)

    def _wait_busy(self):
        self._gpio_busy.wait_for_press()

    def _send_command(self, command):
        self._gpio_dc.off()
        self._spi.writebytes([command])

    def _send_data(self, data):
        self._gpio_dc.on()
        self._spi.writebytes([data])

    def sleep(self):
        logging.info('mock: enter sleep mode')

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
