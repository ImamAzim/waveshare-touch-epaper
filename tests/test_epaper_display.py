import unittest


from waveshare_touch_epaper import epaper_models


class TestEPD2in13Mock(unittest.TestCase):

    def test_mock_interface(self):
        epd = epaper_models['EPD2in13Mock']()



if __name__ == '__main__':
    pass
