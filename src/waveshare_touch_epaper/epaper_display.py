from abc import ABCMeta, abstractmethod
import logging

epaper_models = dict()


class MetaEpaper(ABCMeta):

    """meta class  for epaper displays to store class and their model in a dict"""

    def __init__(cls, name, bases, dict):
        """store the class and in a dict upon creation"""
        ABCMeta.__init__(cls, name, bases, dict)
        epaper_models[name] = cls
