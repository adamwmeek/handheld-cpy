import board
import busio
import terminalio
import time
import displayio
import adafruit_ili9341
from adafruit_display_text import label
from bbq10keyboard import BBQ10Keyboard, STATE_PRESS
import gc
import math


spi = board.SPI()
tft_cs = board.D9
tft_dc = board.D10

SCREEN_BUFF_LEN = 15
screen_lines = []
command = ''

displayio.release_displays()
display_bus = displayio.FourWire(spi, command=tft_dc, chip_select=tft_cs)

display = adafruit_ili9341.ILI9341(display_bus, width=320, height=240)

# Make the display context
window = displayio.Group()
output_window = displayio.Group()
display.show(window)

# Draw background
color_bitmap = displayio.Bitmap(320, 240, 1)
color_palette = displayio.Palette(1)
color_palette[0] = 0x00FF 

bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
window.append(bg_sprite)

# Draw output window
inner_bitmap = displayio.Bitmap(312, 200, 1)
inner_palette = displayio.Palette(1)
inner_palette[0] = 0x000000 
output_grid = displayio.TileGrid(inner_bitmap, pixel_shader=inner_palette, x=4, y=4)
window.append(output_grid)
window.append(output_window)

# Draw text input window
inner_bitmap = displayio.Bitmap(312, 28, 1)
inner_palette = displayio.Palette(1)
inner_palette[0] = 0x000000 
command_window = displayio.TileGrid(inner_bitmap, pixel_shader=inner_palette, x=4, y=208)
command_group = displayio.Group(scale=1, x=12, y=220)
command_label = label.Label(terminalio.FONT, text=command, color=0xFFFFFF)
command_group.append(command_label)
window.append(command_window)
window.append(command_group)

i2c = busio.I2C(board.SCL, board.SDA)
kbd = BBQ10Keyboard(i2c)

# kbd.backlight = 0.5

def reload_lines():
    global output_window

    for i in range(len(output_window)):
        output_window.pop()

    for i in range(len(screen_lines)):
        text_group = displayio.Group(scale=1, x=12, y=12 *(i + 1) )
        text_area = label.Label(terminalio.FONT, text=screen_lines[i], color=0xFFFFFF)
        text_group.append(text_area)
        output_window.append(text_group)

def screen_print_ln(text):
    global output_window

    screen_lines_len = len(screen_lines)
    if screen_lines_len < SCREEN_BUFF_LEN:
        screen_lines.append(text)
        text_group = displayio.Group(scale=1, x=12, y=12 *(screen_lines_len + 1) )
        text_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF)
        text_group.append(text_area)
        output_window.append(text_group)
    else:
        del screen_lines[0]
        screen_lines.append(text)
        gc.collect()
        reload_lines()

def handle_keyboard(pressed):
    global command, command_label, command_group

    if pressed == '\b':
        command = command[:-1]
    elif pressed == '\n': 

        screen_print_ln('> '+ command)

        if '=' in command and not '==' in command:
            try:
                exec(command)
                screen_print_ln('')
            except:
                screen_print_ln('Exception')
        else:
            try:
                result = eval(command)
                if result is None:
                    result = ''
                
                screen_print_ln(str(result))
            except:
                screen_print_ln('Exception')
        
        command = ''
    elif pressed == '`':
        command = command + '='
    else:
        command = command + pressed

    command_group.pop()
    command_label = label.Label(terminalio.FONT, text=command, color=0xFFFFFF)
    command_group.append(command_label)
    time.sleep(0.03)

screen_print_ln('CircuitPython Terminal Started')

while True:
    key_count = kbd.key_count
    if key_count > 0:
        key = kbd.key
        if key[0] == 1:
            handle_keyboard(key[1])