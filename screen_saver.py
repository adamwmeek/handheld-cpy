from program import Program
import time
import gc
import random

import terminalio
import displayio
import sdcardio
import storage

class ScreenSaver(Program):

    def __init__(self, window, spi, sdcard_cs):
        super().__init__(window, spi, sdcard_cs)

    ###
    # UI methods
    ###
    def switch_to(self):
        super().switch_to()

        super().draw_border()
        
        # Draw initial square
        self.square_x = random.randint(4, 290)
        self.square_y = random.randint(4, 220)
        self.square_x_dir = -3
        self.square_y_dir = -2
        self.square_colors = [0xFFFFFF, 0xFF0000, 0x00FF00, 0xFFFF00, 0x7700FF, 0x00FFFF, 0xFF7700]
        self.square_color = random.choice(self.square_colors)
        self.square_first = True
        self.draw_square()
        
    def switch_from(self):
        super().switch_from()

    def handle_keyboard(self, pressed):
            
        if pressed == 'a' or pressed == 's' or pressed == 'd' or pressed == 'w':
            self.square_color = random.choice(self.square_colors)

        gc.collect()
        super().sleep(0.03)

    def tick(self):

        current_time = super().get_time()

        if current_time - self.periodic_time > 10:
                self.square_color = random.choice(self.square_colors)
                self.periodic_time = current_time

        self.square_x += self.square_x_dir
        self.square_y += self.square_y_dir

        if self.square_x <= 4 or self.square_x >= 290:
            self.square_x_dir *= -1
        if self.square_y <= 4 or self.square_y >= 210:
            self.square_y_dir *= -1 

        self.draw_square()
        super().sleep(0.05)

    ########
    # Helpers
    ########
    def draw_square(self):
        super().draw_square(self.square_x, self.square_y, self.square_color)
        