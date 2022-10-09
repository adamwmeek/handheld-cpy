import gc
import math
import random
import time

import board
import busio
import displayio
import adafruit_ili9341
from adafruit_display_text import label
from bbq10keyboard import BBQ10Keyboard
import neopixel
from analogio import AnalogIn

from terminal import Terminal
from editor import Editor

spi = board.SPI()
tft_cs = board.D9
tft_dc = board.D10
sdcard_cs = board.D5

i2c = busio.I2C(board.SCL, board.SDA)
kbd = BBQ10Keyboard(i2c)
pix = neopixel.NeoPixel(board.D11, 1)

current_program = None
backlight_timer = time.time()
periodic_time = time.time()
ambient_light = AnalogIn(board.A3)

# Make main window group
displayio.release_displays()
display_bus = displayio.FourWire(spi, command=tft_dc, chip_select=tft_cs)
display = adafruit_ili9341.ILI9341(display_bus, width=320, height=240)
window = displayio.Group()
display.show(window)

backlight_on_power = 1.0
backlight_on = True
backlight_timeout_sec = 60
backlight_timesout = True

def poff():
    pix[0] = (0, 0, 0)

def set_bk_amb_light():
    global backlight_on_power

    amb_percent = (ambient_light.value - 100) / 700
    amb_percent = amb_percent if amb_percent < 1.0 else 1.0

    backlight_on_power = amb_percent


def draw_window_border():
    global window

    color_bitmap = displayio.Bitmap(320, 240, 1)
    color_palette = displayio.Palette(1)
    color_palette[0] = 0x00FF 

    bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
    window.append(bg_sprite)

set_bk_amb_light()
kbd.backlight = backlight_on_power
kbd.backlight2 = backlight_on_power

draw_window_border()

# Start 'programs'
t = Terminal(window, spi, sdcard_cs)
e = Editor(window, spi, sdcard_cs)

class DummyProg:
    def switch_to(self):
        pass
    def switch_from(self):
        pass
    def handle_keyboard(self, pressed):
        switch_to(t)

dummy = DummyProg()

def switch_to(new_prog=None):
    global current_program
    
    safe_exit = True
    if current_program is not None:
        safe_exit = current_program.switch_from()

    if not safe_exit:
        return

    for x in window:
        window.pop()
    gc.collect()
    draw_window_border()
    current_program = new_prog
    current_program.switch_to()

switch_to(t)

while True:
    # check if it's time to dim the device
    if time.time() - backlight_timer > backlight_timeout_sec and backlight_timesout:
        kbd.backlight = 0.01
        kbd.backlight2 = 0.01
        backlight_on = False

    # check if it's time to run periodic task
    if time.time() - periodic_time > 5:
        set_bk_amb_light()
        periodic_time = time.time()
        if backlight_on:
            kbd.backlight = backlight_on_power
            kbd.backlight2 = backlight_on_power

    key_count = kbd.key_count
    if key_count > 0:
        backlight_timer = time.time()
        
        if not backlight_on:
            kbd.backlight = backlight_on_power
            kbd.backlight2 = backlight_on_power
            backlight_on = True
        key = kbd.key
        if key[0] == 1:
            if key[1] == chr(6):
                switch_to(t)
            elif key[1] == chr(17):
                switch_to(e)
            else:
                current_program.handle_keyboard(key[1])