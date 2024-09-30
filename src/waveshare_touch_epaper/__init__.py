import os


from waveshare_touch_epaper.touch_screen import touchscreen_models
from waveshare_touch_epaper.epaper_display import epaper_models


os.environ['GPIOZERO_PIN_FACTORY'] = 'rpigpio'
