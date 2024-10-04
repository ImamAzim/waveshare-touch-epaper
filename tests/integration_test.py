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
            epd.display(img, full=True)
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
                        epd.display(img, full=False)
                    except EpaperException:
                        epd.display(img, full=True)
    except KeyboardInterrupt:
        print('goodbye')


if __name__ == '__main__':
    touch_and_display_loop()
