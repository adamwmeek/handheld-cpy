import gc
import time

import board
import busio
import displayio
import adafruit_ili9341
from bbq10keyboard import BBQ10Keyboard
import neopixel
from analogio import AnalogIn
from adafruit_display_text import label
import terminalio

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

        self.in_error_screen = False
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

    def draw_error_screen(self, error_lines=['Unknown Error Occurred'], press_to_continue=True):
        global window

        self.in_error_screen = True

        color_bitmap = displayio.Bitmap(320, 240, 1)
        color_palette = displayio.Palette(1)
        color_palette[0] = 0xFF0000

        bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
        self.window.append(bg_sprite)
        output_group = displayio.Group()

        text_group = displayio.Group(scale=1, x=12, y=12)
        text_area = label.Label(terminalio.FONT, text="Oops :(", color=0xFFFFFF)
        text_group.append(text_area)
        output_group.append(text_group)

        num_err_lines = len(error_lines)

        for i in range(num_err_lines):
            text_group = displayio.Group(scale=1, x=12, y=12 *(i + 2) )
            text_area = label.Label(terminalio.FONT, text=error_lines[i], color=0xFFFFFF)
            text_group.append(text_area)
            output_group.append(text_group)

        self.window.append(output_group)

        time.sleep(4)

        if press_to_continue:
            i = num_err_lines + 3
            text_group = displayio.Group(scale=1, x=12, y=12 * i )
            text_area = label.Label(terminalio.FONT, text="Press any key to continue", color=0xFFFFFF)
            text_group.append(text_area)
            output_group.append(text_group)
        else:
            time.sleep(4)

        gc.collect()

    def switch_to(self, new_prog):
        
        if new_prog is None:
            raise Exception('Cannot switch to NoneType program')
        
        safe_exit = True
        if self.current_program is not None:
            safe_exit = self.current_program.switch_from()

        if not safe_exit:
            raise Exception('Failed to switch from previous program')

        for x in self.window:
            self.window.pop()
            
        gc.collect()
        self.draw_window_border()
        self.current_program = new_prog
        self.current_program.switch_to()

    def toggle_flashlight(self):
        if self.flashlight_on:
            self.flashlight[0] = (0, 0, 0)
        else:
            self.flashlight[0] = (255, 255, 255)
        self.flashlight_on = not self.flashlight_on
        time.sleep(0.1)

if __name__ == '__main__':
    global wd
    wd = '/'
    
    system = System()

    # Start 'programs'
    t = Terminal(system.window, system.spi, system.sdcard_cs)
    e = Editor(system.window, system.spi, system.sdcard_cs)
    s = ScreenSaver(system.window, system.spi, system.sdcard_cs)

    def_program = t
    started = False

    try:
        system.switch_to(def_program)
        started = True
    except Exception as e:
        system.draw_error_screen(['Failed to start default program', 'System will now close'] + str(e).splitlines(), press_to_continue=False)

    while started:

        key_count = system.kbd.key_count

        if key_count > 0:
            backlight_timer = time.time()

            if system.in_error_screen:
                system.in_error_screen = False
                system.switch_to(def_program)
                continue
            
            if not system.backlight_on:
                system.kbd.backlight = system.backlight_on_power
                system.kbd.backlight2 = system.backlight_on_power
                system.backlight_on = True

            key = system.kbd.key
            pressed = key[1]

            try:
                if pressed == chr(6):
                    system.switch_to(t)

                elif pressed == chr(17):
                    system.switch_to(e)

                elif pressed == chr(7):
                    system.switch_to(s)

                elif pressed == chr(18):
                    system.toggle_flashlight()
                    
                else:
                    system.current_program.handle_keyboard(pressed)
            except Exception as e:
                system.draw_error_screen(str(e).splitlines())
                continue

            gc.collect()
            time.sleep(0.05)

        if system.in_error_screen:
            continue

        try:
            system.current_program.tick()
        except Exception as e:
            system.draw_error_screen(str(e).splitlines())
            continue
        
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