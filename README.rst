waveshare touch epaper
=========================

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

   pip install waveshare-touch-epaper

If you work in a virtual environement, you will need first:

.. code-block:: bash

    sudo apt-get install python3-pip
    sudo apt-get install python3-venv


Usage
========

we show first a full example issued from the test, then we look at each feature in details.

full example
-----------------

full script to use the epd display and its touch screen (2in13). everytime we touch the screen, it draw a point.

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


import classes
------------------

you can either import directly the classes in the epaper_display and touch_screen module:

.. code-block:: python

        from waveshare_touch_epaper.epaper_display import EPD2in13, EpaperException
        from waveshare_touch_epaper.touch_screen import GT1151, TouchEpaperException


        epd = EPD2in13()

or you can use the following dictionary to get all the available classes:

.. code-block:: python
   from waveshare_touch_epaper import touch_screen_models, epaper_models


   print(epaper_models.keys())
   epd = epaper_models['EPD2in13']


start and stop
__________________________

to use the epd or the touch screen, you need to open the port, reset, etc. At the end, it is better to close the object to close the port and put in sleep mode to reduce consumption. This is done with the open/close and start/stop method:

.. code-block:: python
   epd.start()
   # display some stuff..
   epd.stop()
   gt.open()
   # read input of touch screen
   gt.close()

and this can also be done in a context manager:

.. code-block:: python
   with EPD2in13() as epd:
       pass
       # display some stuff
   with GT1151() as gt:
       pass
       # read some input

display images
-----------------

with the epaper display class you can access the dimensions, and display some images:

.. code-block:: python
   from PIL import Image


   width = epd.WIDTH
   height = epd.HEIGHT
   img = Image.new('1', (width, height), 255)
   epd.display(img)

by default this will make a full refresh. you can also use a partial refresh:

.. code-block:: python
   epd.display(img, full_refresh=False)

however, after a certain number of consecutive partial display, it will raise an error so that you can only do a full refresh. Do handle this case without counting the number of partial refresh you can use a try/except:

.. code-block:: python
    try:
        epd.display(img, full_refresh=False)
    except EpaperException:
        epd.display(img)

and it is possible to clear the image:

.. code-block:: python
   epd.clear()  # all the sreen becomes white
   epd.clear(0)  # all the screen becomes black

touch screen input read
--------------------------

one can read the input of the touch screen:

.. code-block:: python
   x, y, s = gt.input()  # x, y coordinates, s size of touch

the method will block until a touch is detected (and only if it is different from the previous coordinates). you can add a timeout, so that it will raise a TouchEpaperException if no touch is detected during this time:

.. code-block:: python
   x, y, s = gt.input(timeout=30)  # raise exception if no touch after 30s

touch screen can be set in sleep mode to reduce consumption. It will be set back in normal mode automaticely when we ask for input:

.. code-block:: python
   gt.sleep()

one can also switch to gesture mode and wait for specific gesture (slide_left, slide_right, etc...)
.. code-block:: python
   gt.wait_for_gesture(gesture='left_slide')

The method will block until such gesture is detected. possible gesture are (right_slide, left_slide, slide_up, slide_down, double_click,)

mock mode
-------------

there a mock classes:

.. code-block:: python
   epd = epaper_models['EPD2in13Mock']
   gt = epaper_models['GT1151Mock']

there is no need of the waveshare device nor any gpio or i2c port (so an desktop computer). The display uses the show method of PIL and the input comes from the keyboard.


Features
========

* control the eink displays from waveshare
* control the touch screen from waveshare


License
=======

The project is licensed under MIT license
