waveshare touch epaper
=========================

a copy of the waveshare python library `waveshare library <https://github.com/waveshareteam/Touch_e-Paper_HAT>`_ for the Touch epaper display 2.13 inches and 2.9 inches. Like this, you can directly use pip to install the library in your virtual environement, without the need to clone or download all the files.

hardware requirements
=======================

* one of the waveshare touch epaper display
* raspberry pi (or probably an other computer with an gpio port and spi interface)

Installation
============

.. code-block:: bash

    pip install git+https://github.com/ImamAzim/waveshare-touch-epaper.git

Usage
========


import and create instances of display and touch screen:

.. code-block:: python

    import waveshare_touch_epaper
    from waveshare_touch_epaper import epd2in13_V4 # to import module for other device, use dir function on the package name
    from waveshare_touch_epaper import gt1151 # module of touch screen
    epd = epd2in13_V4.EPD()
    gt = gt1151.GT1151()

Then, you can follow the `examples <https://github.com/waveshareteam/Touch_e-Paper_HAT/tree/main/python/examples>`_ from the waveshare team.
    


Features
========

* control the eink displays from waveshare
* control the touch screen from waveshare


License
=======

The project is licensed under MIT license
