waveshare touch epaper
=========================
in development
a refactor of python library `waveshare library <https://github.com/waveshareteam/Touch_e-Paper_HAT>`_ for the Touch epaper display 2.13 inches, more pythonic and easier to use. Like this, you can directly use pip to install the library in your virtual environement, without the need to clone or download all the files.

hardware requirements
=======================

* one of the waveshare touch epaper display (currentyl only the 2.13 inch)
* raspberry pi (or probably an other computer with an gpio port and spi interface)

Installation
============

be sure that you have activated the spi and i2c interface. On the raspberry pi:

.. code-block:: bash

    sudo raspi-config nonint do_spi 1
    sudo raspi-config nonint do_i2c 1

and then you can install the package with pip

.. code-block:: bash

    pip install git+https://github.com/ImamAzim/waveshare-touch-epaper.git

If you work in a virtual environement, you will need first:

.. code-block:: bash

    sudo apt-get install python3-pip
    sudo apt-get install python3-venv


Usage
========

To use a epaper display (to be changed):
here is a full example to load the epd display and its touch screen. everytime we touch the screen, it draw a point.

.. code-block:: python

        from PIL import Image, ImageDraw


        from waveshare_touch_epaper.epaper_display import EPD2in13, EpaperException
        from waveshare_touch_epaper.touch_screen import GT1151, TouchEpaperException


        def touch_and_display_loop():
            try:
                width = EPD2in13.WIDTH
                height = EPD2in13.HEIGHT
                img = Image.new('1', (width, height), 255)
                draw = ImageDraw.Draw(img)
                draw.text((width/2, height/2), 'touch me!')
                with GT1151() as gt, EPD2in13() as epd:
                    epd.display(img)
                    while True:
                        try:
                            x, y, s = gt.input(timeout=30)
                        except TouchEpaperException:
                            print('no touch detected during timeout, exit')
                            break
                        else:
                            length = s ** 0.5
                            dx = length / 2
                            draw.rectangle((x - dx, y - dx, x + dx, y + dx), fill=0)
                            try:
                                epd.display(img, full_refresh=False)
                            except EpaperException:
                                epd.display(img)
            except KeyboardInterrupt:
                print('goodbye')

Features
========

* control the eink displays from waveshare
* control the touch screen from waveshare


License
=======

The project is licensed under MIT license
