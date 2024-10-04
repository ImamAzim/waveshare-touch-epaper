from abc import ABCMeta, abstractmethod 
import logging


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
    """mock interface for epaper display, 2.13 inch. no need of gpio, the image are displayed
    on the screen with pillow module"""

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

    def __init__(self):
        """initialise epd

        """
        self._remaining_partial_refresh = None

    def full_update(self):
        logging.info('full update mock')

    def _partial_update(self):
        logging.info('partial update mock')

    def clear(self):
        img = Image.new('1', (self.WIDTH, self.HEIGHT), 255)
        img.show()

    def open(self):
        logging.info('mock open port epd')
        spi     = spidev.SpiDev(0, 0)
        # GPIO_RST_PIN    = gpiozero.LED(EPD_RST_PIN)
        # GPIO_DC_PIN     = gpiozero.LED(EPD_DC_PIN)
        # GPIO_BUSY_PIN   = gpiozero.Button(EPD_BUSY_PIN, pull_up = False)

    def close(self):
        logging.info('mock close port epd')

    def sleep(self):
        logging.info('mock: enter sleep mode')

    def display(self, img: Image.Image, full=True, wait=False):
        if full:
            pass
            self._remaining_partial_refresh = self._MAX_PARTIAL_REFRESH
            self._partial_update()
        else:
            if self._remaining_partial_refresh == 0:
                msg = 'too many consecutive partial refresh. need a full refresh'
                raise EpaperException(msg)
            self._remaining_partial_refresh -= 1

    def __enter__(self):
        self.open()
        self.full_update()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.sleep()
        self.close()
