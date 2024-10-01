from abc import ABCMeta, abstractmethod, abstractproperty
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
    @abstractproperty
    def WIDTH(self) -> int:
        """width of screen in number of pixels"""
        pass

    @abstractproperty
    def HEIGHT(self) -> int:
        """height of screen in number of pixels"""
        pass

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
        after exiting sleep mode or for a full refresh

        """
        pass

    @abstractmethod
    def partial_update(self):
        """should be called after an image is displayed with full refresh
        :returns: TODO

        """
        pass

    @abstractmethod
    def display(self, img: Image.Image, full: bool):
        """send img to epaper RAM and do a full or partial refresh

        :img: that will be displayed
        :full: if True, apply a full refresh, otherise a partial one
        :raise EpaperException: when img has incorrect dimension (WIDTH, HEIGHT)

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
    """for this mock, no need of gpio port or spi and epaper display.
    image are shown on desktop with pillow"""

    @property
    def WIDTH(self):
        return 250

    @property
    def HEIGHT(self):
        return 122

    def full_update(self):
        logging.info('full update mock')

    def partial_update(self):
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
    pass
