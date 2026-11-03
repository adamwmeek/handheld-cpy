###############################################
## program.py
## 
## Provides a template for programs to be run on 
## the handheld device.
##
###############################################
import time
import gc
import os

import terminalio
import displayio
import sdcardio
import storage

from adafruit_display_text import label

class Program:

    # Sets system level variables for the program to use
    # Overriding classes need to call super().__init__()
    # at the start of their constructor
    def __init__(self, window, spi, sdcard_cs):
        self.window = window
        self.spi = spi
        self.sdcard_cs = sdcard_cs
        self.old_print = None
        self.output_group = displayio.Group()
        self.command_group = None
        self.periodic_time = time.time()
        self.wd = '/'
        self.input_drawn = False
        self.text_output_drawn = False
        self.sd_mounted = False
        

    # Provides a base line context switching
    # Overriding classes need to call super().switch_to()
    # at the start of their switch_to() method
    def switch_to(self):
        global print
        # global wd

        self.old_print=print
        # self.wd = wd
        self.wd = '/'
        self.periodic_time = time.time()

    # Provides a base line context switching
    # Overriding classes need to return super().switch_from()
    # at the end of their switch_from() method
    def switch_from(self):
        # global print
        # global wd
        # wd = self.wd
        # print=self.old_print

        return True

    # The following methods are required to be implemented 
    # by inheriting classes

    # handle_keyboard() is called when a key is pressed
    def handle_keyboard(self, pressed):
        pass

    # tick() is called periodically to allow the program to update
    def tick(self):
        pass

    # The following methods are helpers that can simplify 
    # common tasks, such as graphics, file I/O, etc.


    def get_time(self):
        return time.time()


    def sleep(self, seconds):
        # gc.collect()
        time.sleep(seconds)


    def draw_border(self):
        inner_bitmap = displayio.Bitmap(312, 230, 1)
        inner_palette = displayio.Palette(1)
        inner_palette[0] = 0x000000 
        output_grid = displayio.TileGrid(inner_bitmap, pixel_shader=inner_palette, x=4, y=4)
        self.window.append(output_grid)
        self.window.append(self.output_group)


    def draw_input_window(self, x, y):
        if not self.input_drawn:
            inner_bitmap = displayio.Bitmap(312, 28, 1)
            inner_palette = displayio.Palette(1)
            inner_palette[0] = 0x000000 
            command_grid = displayio.TileGrid(inner_bitmap, pixel_shader=inner_palette, x=x, y=y)
            self.window.append(command_grid)
            self.window.append(self.command_group)
            command_label = label.Label(terminalio.FONT, text=self.command, color=0xFFFFFF)
            self.command_group.append(command_label)
            self.input_drawn = True

    ## TODO
    def update_input_window(self, text):
        if self.input_drawn:
            self.window.pop()


    ## TODO
    def draw_text_output_window(self, x, y):
        if not self.text_output_drawn:
            # inner_bitmap = displayio.Bitmap(312, 170, 1)
            # inner_palette = displayio.Palette(1)
            # inner_palette[0] = 0x000000 
            # output_grid = displayio.TileGrid(inner_bitmap, pixel_shader=inner_palette, x=x, y=y)
            # self.window.append(output_grid)
            # self.window.append(self.output_group)
            self.text_output_drawn = True


    ## TODO
    def update_text_output_window(self, text):
        if self.text_output_drawn:
            self.window.pop()


    def draw_square(self, x, y, color):
        bitmap = displayio.Bitmap(30, 30, 1)
        palette = displayio.Palette(1)
        palette[0] = self.square_color
        grid = displayio.TileGrid(bitmap, pixel_shader=palette, x=x, y=y)
        
        if not self.square_first:
            self.output_group.pop()
        else:
            self.square_first = False

        self.output_group.append(grid)
        
        gc.collect()


    def mount(self):

        if not self.sd_mounted:
            sdcard = sdcardio.SDCard(self.spi, self.sdcard_cs)
            vfs = storage.VfsFat(sdcard)

            try:
                storage.mount(vfs, "/sd")
            except OSError:
                return False
            
            self.sd_mounted = True

        return True


    def unmount(self):
        
        if self.sd_mounted:
            storage.umount("/sd")
            self.sd_mounted = False

        return True


    def cd(self, path='/'):
    
        if not path.endswith('/'):
            path+='/'

        if path.startswith('./'):
            self.wd+=path[2:]
        elif path.startswith('/'):
            self.wd=path
        else:
            if not self.wd.endswith('/'):
                self.wd+='/'
            self.wd+=path


    def cp(self, old, new):

        if self.sd_mounted:
            chunk_size = 1024
    
            if old.startswith('./'):
                old=self.wd+old[2:]
            elif old.startswith('/'):
                pass
            else:
                old=self.wd+old
            
            if new.startswith('./'):
                new=self.wd+new[2:]
            elif new.startswith('/'):
                pass
            else:
                new=self.wd+new
    
            old_file = open(old, 'rb')
            new_file = open(new, 'wb')
    
            while True:
                chunk = old_file.read(chunk_size)
                if chunk == b'':
                    break
                new_file.write(chunk)
    
            old_file.close()
            new_file.close()
            gc.collect()
            

    def mkdir(self, path):

        if self.sd_mounted:
    
            if path.startswith('./'):
                path=self.wd+path[2:]
            elif path.startswith('/'):
                pass
            else:
                path=self.wd+path
            
            os.mkdir(path)
