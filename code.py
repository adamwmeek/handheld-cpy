import gc
import time

import board
import busio
import displayio
import adafruit_ili9341
from bbq10keyboard import BBQ10Keyboard
import neopixel
from analogio import AnalogIn

from terminal import Terminal
from editor import Editor
from screen_saver import ScreenSaver

class System:
    def __init__(self):

        self.spi = board.SPI()
        self.tft_cs = board.D9
        self.tft_dc = board.D10
        self.sdcard_cs = board.D5
        
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.kbd = BBQ10Keyboard(self.i2c)
        self.pix = neopixel.NeoPixel(board.D11, 1)
        self.flashlight = neopixel.NeoPixel(board.NEOPIXEL, 1)

        self.current_program = None
        self.backlight_timer = time.time()
        self.periodic_time = time.time()
        self.ambient_light = AnalogIn(board.A3)

        # Make main window group
        displayio.release_displays()
        display_bus = displayio.FourWire(self.spi, command=self.tft_dc, chip_select=self.tft_cs)
        self.display = adafruit_ili9341.ILI9341(display_bus, width=320, height=240)
        self.window = displayio.Group()
        self.display.show(self.window)

        self.backlight_on_power = 1.0
        self.backlight_on = True
        self.backlight_timeout_sec = 60
        self.backlight_timesout = True
        self.flashlight_on = False

        self.set_bk_amb_light()
        self.kbd.backlight = self.backlight_on_power
        self.kbd.backlight2 = self.backlight_on_power

        self.draw_window_border()
        gc.collect()

    def poff(self):
        self.pix[0] = (0, 0, 0)

    def set_bk_amb_light(self):
        global backlight_on_power

        amb_percent = (self.ambient_light.value - 100) / 700
        amb_percent = amb_percent if amb_percent < 1.0 else 1.0

        self.backlight_on_power = amb_percent

    def draw_window_border(self):
        global window

        color_bitmap = displayio.Bitmap(320, 240, 1)
        color_palette = displayio.Palette(1)
        color_palette[0] = 0x00FF 

        bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
        self.window.append(bg_sprite)

    def draw_error_screen(self):
        global window

        color_bitmap = displayio.Bitmap(320, 240, 1)
        color_palette = displayio.Palette(1)
        color_palette[0] = 0xFF0000

        bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
        self.window.append(bg_sprite)

        time.sleep(5)

    def switch_to(self, new_prog=None):
        
        if new_prog is None:
            return False
        
        safe_exit = True
        if self.current_program is not None:
            safe_exit = self.current_program.switch_from()

        if not safe_exit:
            return False

        # for x in self.window:
        #     x.pop()
            
        gc.collect()
        self.draw_window_border()
        self.current_program = new_prog
        self.current_program.switch_to()

        return True

    def toggle_flashlight(self):
        if self.flashlight_on:
            self.flashlight[0] = (0, 0, 0)
        else:
            self.flashlight[0] = (255, 255, 255)
        self.flashlight_on = not self.flashlight_on

if __name__ == '__main__':
    global wd
    wd = '/'
    
    system = System()

    # Start 'programs'
    t = Terminal(system.window, system.spi, system.sdcard_cs)
    e = Editor(system.window, system.spi, system.sdcard_cs)
    s = ScreenSaver(system.window, system.spi, system.sdcard_cs)

    started = system.switch_to(s)

while started:
    # check if it's time to dim the device
    if time.time() - system.backlight_timer > system.backlight_timeout_sec and system.backlight_timesout and system.current_program != s:
        system.kbd.backlight = 0.01
        system.kbd.backlight2 = 0.01
        system.backlight_on = False

    # check if it's time to run periodic task
    if time.time() - system.periodic_time > 5:
        system.set_bk_amb_light()
        system.periodic_time = time.time()
        if system.backlight_on:
            system.kbd.backlight = system.backlight_on_power
            system.kbd.backlight2 = system.backlight_on_power

    key_count = system.kbd.key_count

    if key_count > 0:
        backlight_timer = time.time()
        
        if not system.backlight_on:
            system.kbd.backlight = system.backlight_on_power
            system.kbd.backlight2 = system.backlight_on_power
            system.backlight_on = True

        key = system.kbd.key


        switch_success = False
        try:
            if key[0] == chr(19):
                switch_success = system.switch_to(s)
            elif key[0] == chr(17):
                switch_success = system.switch_to(e)
            elif key[0] == chr(7):
                switch_success = system.switch_to(t)
            elif key[0] == chr(18):
                system.toggle_flashlight()
                switch_success = True
            else:
                system.current_program.handle_keyboard(key[0])
        except Exception as e:
            system.draw_error_screen()

    system.current_program.tick()