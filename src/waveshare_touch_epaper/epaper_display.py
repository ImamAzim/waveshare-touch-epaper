from abc import ABCMeta, abstractmethod, abstractproperty
import logging

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
    def WIDTH(self):
        pass

    @abstractproperty
    def HEIGHT(self):
        pass



class EPD2in13Mock(BaseEpaper, metaclass=MetaEpaper):

    @property
    def WIDTH(self):
        return 250

    @property
    def HEIGHT(self):
        return 122


class EpaperException(Exception):
    pass


class EPD2in13(BaseEpaper, metaclass=MetaEpaper):
    pass
