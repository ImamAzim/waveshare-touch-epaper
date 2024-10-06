import unittest
import time


from PIL import Image, ImageDraw

from waveshare_touch_epaper import epaper_models


class TestEPD2in13Mock(unittest.TestCase):

    def test_mock_interface(self):
        epd = epaper_models['EPD2in13Mock']()

def display():
    with epaper_models['EPD2in13'] as epd:
        img = Image.new('1', (epd.WIDTH, epd.HEIGHT), 255)
        draw = ImageDraw.Draw(img)
        x0 = epd.WIDTH // 2
        y0 = epd.HEIGHT // 2
        draw.text(x0, y0, 'hello world')
        epd.display(img)


if __name__ == '__main__':
    display()
