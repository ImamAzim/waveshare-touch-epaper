from abc import ABCMeta, abstractmethod
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
    pass


class EPD2in13Mock(BaseEpaper, metaclass=MetaEpaper):
    pass


class EpaperException(Exception):
    pass


class EPD2in13(BaseEpaper, metaclass=MetaEpaper):
    pass
