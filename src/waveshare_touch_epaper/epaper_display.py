import time
from abc import ABCMeta, abstractmethod
import logging


import spidev
import gpiozero
from PIL import Image


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

    WIDTH: int = NotImplemented
    """width of screen in number of pixels"""

    HEIGHT: int = NotImplemented
    """height of screen in number of pixels"""

    @abstractmethod
    def open(self):
        """open the spi and gpio port

        """
        pass

    @abstractmethod
    def __enter__(self):
        """open port and full update
        :returns: self

        """
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_value, traceback):
        """exit the context manager. enter sleep mode and close all ports

        :exc_type: None if exited without exception
        :exc_value: None if exited without exception
        :traceback: None if exited without exception

        """
        pass

    @abstractmethod
    def close(self):
        """close the port so that display consume 0V

        """
        pass

    # @abstractmethod
    # def full_update(self):
        # """initialization. should be called when the screen start working,
        # after exiting sleep mode or possibly before full refresh

        # """
        # pass

    @abstractmethod
    def display(self, img: Image.Image, full: bool, wait: bool):
        """send img to epaper RAM and do a full or partial refresh
        (partial update will be called if full refresh)

        :img: that will be displayed
        :full: if True, apply a full refresh, otherise a partial one
        :wait: if True will wait for busy PIN(?)
        :raise EpaperException: when img has incorrect dimension

        """
        pass

    @abstractmethod
    def clear(self):
        """clear the e-paper to white

        """
        pass

    # @abstractmethod
    # def sleep(self):
        # """enter deep sleep mode

        # """
        # pass


class EPD2in13Mock(BaseEpaper, metaclass=MetaEpaper):
    """mock interface for epaper display, 2.13 inch. no need of gpio,
    the image are displayed on the screen with pillow module"""

    WIDTH = 122
    HEIGHT = 250

    def full_update(self):
        logging.info('full update mock')

    def _partial_update(self):
        logging.info('partial update mock')

    def clear(self):
        img = Image.new('1', (self.WIDTH, self.HEIGHT), 255)
        img.show()

    def open(self):
        logging.info('mock open port epd')

    def close(self):
        logging.info('mock close port epd')

    def sleep(self):
        logging.info('mock: enter sleep mode')

    def display(self, img: Image.Image, full=True, wait=False):
        img.show()
        if full:
            self._partial_update()

    def __enter__(self):
        self.open()
        self.full_update()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.sleep()
        self.close()


class EpaperException(Exception):
    pass


class EPD2in13(BaseEpaper, metaclass=MetaEpaper):

    WIDTH = 122
    HEIGHT = 250
    _MAX_PARTIAL_REFRESH = 50

    _RST_PIN = 17
    _DC_PIN = 25
    _CS_PIN = 8
    _BUSY_PIN = 24

    _ADRESS = 0x14

    _SPI_MAXSPEED = 10000000
    _SPI_MODE = 0b00

    _COMMAND = dict(
            reset=0x12,
            driver_output_control=0x01,
            data_entry_mode_setting=0x11,
            set_ram_x=0x44,
            set_ram_y=0x45,
            border_waveform_control=0x3c,
            temperature_sensor_control=0x18,
            deep_sleep_mode=0x10,
            display_update_control=0x21,
            set_ram_x_adress_counter=0x4e,
            set_ram_y_adress_counter=0x4f,
            write_ram_bw=0x24,
            write_ram_red=0x26,
            )

    def __init__(self):
        """initialise epd

        """
        self._remaining_partial_refresh = None
        self._gpio_rst = gpiozero.LED(self._RST_PIN)
        self._gpio_dc = gpiozero.LED(self._DC_PIN)
        self._gpio_busy = gpiozero.Button(
                self._BUSY_PIN,
                pull_up=False)
        self._spi = spidev.SpiDev(0, 0)

    def __enter__(self):
        self.open()
        return self

    def open(self):
        self._power_on()
        self._set_initial_configuration()

    def close(self):
        self._power_off()
        self._close_all_port()

    def clear(self, color=0b1, coord=None):
        """
        :color: 1 for white, 0 for black
        :coords: if None, full screen is cleared
        if tuple (x_start, x_end, y_start, y_end) coord of window

        """
        if coords is None:
            x_start = 0
            x_end = self.WIDTH - 1
            y_start = 0
            y_end = self.HEIGHT - 1
        else:
            x_start, x_end, y_start, y_end = coords
        self._send_initialization_code(coord)
        self._load_waveform_lut()
        color = 0b1
        byte_color = 0xff * color
        pixel_byte = byte_color.to_bytes(1, 'big')
        img_bytes = pixel_byte * N
        img = bytearray(img_bytes)
        self._write_image_and_drive_display_panel(x_start, y_start, img=img)

    def display(self, img: Image.Image, full=True, wait=False):
        if full:
            # set init config (hard reset?)
            self._send_initialization_code()
            self._load_waveform_lut()
            self._write_image_and_drive_display_panel()
            self._remaining_partial_refresh = self._MAX_PARTIAL_REFRESH
            self._partial_update()
        else:
            if self._remaining_partial_refresh == 0:
                msg = 'too many partial refresh. need a full refresh'
                raise EpaperException(msg)
            # TODO: set init config (soft reset?)
            # TODO: compute window size for img
            x_start = 0
            y_start = 0
            x_end = 121
            y_end = 249
            coords = (x_start, x_end, y_start, y_end)
            self._send_initialization_code(coords)
            self._write_image_and_drive_display_panel(x_start, y_start)
            self._remaining_partial_refresh -= 1

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def _power_on(self):
        logging.info('power on')
        logging.debug('power cannot be switched because rpi 3.3v connected')
        time.sleep(0.01)

    def _set_initial_configuration(self):
        logging.info('set initial configuration')
        self._spi.max_speed_hz = self._SPI_MAXSPEED
        self._spi.mode = self._SPI_MODE
        self._hw_reset()
        self._send_command('reset')
        time.sleep(0.01)

    def _send_initialization_code(self, coords=None):
        logging.info('send initialization code')
        self._set_gate_driver_output()
        self._set_display_RAM_size(coords)
        self._set_panel_border()
        self._set_display_source_mode()

    def _load_waveform_lut(self):
        self._sense_temperature()
        self._wait_busy_low()

    def _write_image_and_drive_display_panel(self, x_start=0, y_start=0, img: bytearray):
        self._write_img_data_in_ram(x_start, y_start, img)

    def _power_off(self):
        logging.info('power off')
        self._deep_sleep()
        logging.debug('power cannot be switched because rpi 3.3v connected')
        self._gpio_rst.off()
        self._gpio_dc.off()

    def _close_all_port(self):
        self._spi.close()
        self._gpio_rst.close()
        self._gpio_dc.close()
        self._gpio_busy.close()

    def _hw_reset(self):
        self._gpio_rst.on()
        time.sleep(0.02)
        self._gpio_rst.off()
        time.sleep(0.002)
        self._gpio_rst.on()
        time.sleep(0.02)

    def _set_gate_driver_output(self):
        self._send_command('driver_output_control')
        self._send_data(0xf9)
        self._send_data(0x00)
        self._send_data(0x00)

    def _set_display_RAM_size(self, coords):
        """set windows size to be refreshed.

        :coords: if None, full screen is refresh
        if tuple (x_start, x_end, y_start, y_end) coord of window

        """
        if coords is None:
            x_start = 0
            x_end = self.WIDTH - 1
            y_start = 0
            y_end = self.HEIGHT - 1
        else:
            x_start, x_end, y_start, y_end = coords
        self._send_command('data_entry_mode_setting')
        self._send_data(0b011)
        self._send_command('set_ram_x')
        self._send_data(x_start >> 3)  # adress div by 8 as bytes has 8 bits
        self._send_data(x_end >> 3)
        self._send_command('set_ram_y')
        data = y_start
        low_byte, hi_byte = self._split_low_hi_bytes(data)
        self._send_data(low_byte)
        self._send_data(hi_byte)
        data = y_end
        low_byte, hi_byte = self._split_low_hi_bytes(data)
        self._send_data(low_byte)
        self._send_data(hi_byte)

    def _set_panel_border(self):
        self._send_command('border_waveform_control')
        vbd_opt = 0b00 << 6
        vbd_level = 0b00 << 4
        gs_control = 0b1 << 2  # follow LUT
        gs_setting = 0b01  # LUT1
        data = gs_control + gs_setting + vbd_level + vbd_opt
        self._send_data(data)

    def _set_display_source_mode(self):
        self._send_command('display_update_control')
        self._send_data(0x0)
        source_output_mode = 0b1 << 7
        self._send_data(source_output_mode)

    def _sense_temperature(self):
        self._send_command('temperature_sense_control')
        self._send_data(0x80)

    def _write_img_data_in_ram(self, x_start, y_start, img: bytearray):

        self._send_command('set_ram_x_adress_counter')
        self._send_data(x_start>>3)

        self._send_command('set_ram_y_adress_counter')
        low_byte, hi_byte = self._split_low_hi_bytes(y_start)
        self._send_data(low_byte)
        self._send_data(hi_byte)

        self._send_command('write_ram_bw')
        self._send_data_array(img)

    def _wait_busy_low(self):
        self._gpio_busy.wait_for_inactive()

    def _deep_sleep(self):
        self._send_command('deep_sleep_mode')
        # TODO: check deep sleep mode 1 or 2
        self._send_data(0x11)

    def _split_low_hi_bytes(large_byte):
        low_byte = large_byte & 0xff
        hi_byte = large_byte >> 8
        return low_byte, hi_byte

    def _send_command(self, cmd_key: str):
        command = self._COMMAND.get(cmd_key)
        self._gpio_dc.off()
        self._spi.writebytes([command])

    def _send_data(self, data):
        self._gpio_dc.on()
        self._spi.writebytes([data])

    def _send_data_array(self, data_array):
        self._gpio_dc.on()
        self._spi.writebytes(data_array)

    def _partial_update(self):
        logging.info('partial update mock')
