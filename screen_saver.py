import time
import gc
import random

from adafruit_display_text import label
import terminalio
import displayio
import sdcardio
import storage

class ScreenSaver:

    def __init__(self, window, spi, sdcard_cs):
        self.window = window
        self.spi = spi
        self.sdcard_cs = sdcard_cs

        self.output_group = None
        self.old_print = None
        
        self.wd = '/'

    ###
    # UI methods
    ###
    def switch_to(self):
        global print

        self.old_print=print

        self.output_group = displayio.Group()
        
        # Draw output window
        inner_bitmap = displayio.Bitmap(312, 230, 1)
        inner_palette = displayio.Palette(1)
        inner_palette[0] = 0x000000 
        output_grid = displayio.TileGrid(inner_bitmap, pixel_shader=inner_palette, x=4, y=4)
        self.window.append(output_grid)
        self.window.append(self.output_group)
        
        # Draw initial square
        self.square_x = random.randint(4, 290)
        self.square_y = random.randint(4, 220)
        self.square_x_dir = -3
        self.square_y_dir = -2
        self.square_colors = [0xFFFFFF, 0xFF0000, 0x00FF00, 0xFFFF00, 0x7700FF, 0x00FFFF, 0xFF7700]
        self.square_color = random.choice(self.square_colors)
        self.square_first = True
        self.draw_square(self.square_x, self.square_y)
        self.periodic_time = time.time()
        
    def switch_from(self):
        global print

        print = self.old_print
        return True

    def handle_keyboard(self, pressed):
            
        if pressed == 'a' or pressed == 's' or pressed == 'd' or pressed == 'w':
            self.square_color = random.choice(self.square_colors)

        gc.collect()
        time.sleep(0.03)

    def tick(self):

        if time.time() - self.periodic_time > 10:
                self.square_color = random.choice(self.square_colors)
                self.periodic_time = time.time()

        self.square_x += self.square_x_dir
        self.square_y += self.square_y_dir

        if self.square_x <= 4 or self.square_x >= 290:
            self.square_x_dir *= -1
        if self.square_y <= 4 or self.square_y >= 210:
            self.square_y_dir *= -1 

        self.draw_square(self.square_x, self.square_y)
        time.sleep(0.05)

    ########
    # Helpers
    ########
    def draw_square(self, x, y):
        bitmap = displayio.Bitmap(30, 30, 1)
        palette = displayio.Palette(1)
        palette[0] = self.square_color
        grid = displayio.TileGrid(bitmap, pixel_shader=palette, x=x, y=y)
        if not self.square_first:
            self.output_group.pop()
        self.output_group.append(grid)
        self.square_first = False
        gc.collect()