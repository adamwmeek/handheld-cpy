from program import Program
import random

class ScreenSaver(Program):

    def __init__(self, window, spi, sdcard_cs):
        super().__init__(window, spi, sdcard_cs)
        self.crash_counter = 0

    ###
    # UI methods
    ###
    def switch_to(self):
        super().switch_to()

        super().draw_border()
        
        # Draw initial square
        self.square_x = random.randint(4, 286)
        self.square_y = random.randint(4, 204)
        self.square_x_dir = random.choice([-5, 5])
        self.square_y_dir = random.choice([-3, 3])
        self.square_colors = [0xFFFFFF, 0xFF0000, 0x00FF00, 0xFFFF00, 0x7700FF, 0x00FFFF, 0xFF7700, 0xFF0077, 0x0077FF, 0x33FF33, 0xFF3333, 0x3333FF, 0xFF33FF, 0x33FFFF, 0xFFFF33]
        self.square_color = random.choice(self.square_colors)
        self.square_colors.remove(self.square_color)
        self.square_first = True
        self.draw_square()

    def handle_keyboard(self, pressed):
            
        if pressed == 'a' or pressed == 's' or pressed == 'd' or pressed == 'w':
            old_color = self.square_color
            self.square_color = random.choice(self.square_colors)
            self.square_colors.append(old_color)
            self.square_colors.remove(self.square_color)

    def tick(self):

        current_time = super().get_time()

        if current_time - self.periodic_time > 10:
                old_color = self.square_color
                self.square_color = random.choice(self.square_colors)
                self.square_colors.append(old_color)
                self.square_colors.remove(self.square_color)
                self.periodic_time = current_time
                # self.crash_counter += 1

        self.square_x += self.square_x_dir
        self.square_y += self.square_y_dir

        if self.square_x <= 4 or self.square_x >= 286:
            self.square_x_dir *= -1
        if self.square_y <= 4 or self.square_y >= 204:
            self.square_y_dir *= -1 

        self.draw_square()
        super().sleep(0.05)

        # if self.crash_counter >= 3:
        #     raise Exception("This is a test crash")

    ########
    # Helpers
    ########
    def draw_square(self):
        super().draw_square(self.square_x, self.square_y, self.square_color)
        