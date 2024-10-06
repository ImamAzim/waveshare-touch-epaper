import unittest
import time


from PIL import Image, ImageDraw

from waveshare_touch_epaper import epaper_models


class TestEPD2in13Mock(unittest.TestCase):

    def test_mock_interface(self):
        epd = epaper_models['EPD2in13Mock']()

def display():
    with epaper_models['EPD2in13']() as epd:
        img = Image.new('1', (epd.WIDTH, epd.HEIGHT), 255)
        draw = ImageDraw.Draw(img)
        x0 = epd.WIDTH // 2
        y0 = epd.HEIGHT // 2
        draw.text((x0, y0), 'hello world')
        t1 = time.time()
        epd.display(img)
        t2 = time.time()
        print(t2-t1)
        for i in range(9, 0, -1):
            x0 = 0
            y0 = epd.HEIGHT // 10 * i
            draw.text((x0, y0), str(i))
            t1 = time.time()
            epd.display(img, full_refresh=False)
            t2 = time.time()
            print(t2-t1)


if __name__ == '__main__':
    display()
