import time
import gc
import os

from adafruit_display_text import label
import terminalio
import displayio
import sdcardio
import storage

class Terminal:

    def __init__(self, window, spi, sdcard_cs):
        self.window = window
        self.spi = spi
        self.sdcard_cs = sdcard_cs

        self.output_group = None
        self.command_group = None
        self.old_print = None

        self.command = ''
        self.SCREEN_BUFF_LEN = 15
        self.screen_lines = ['CircuitPython Terminal Started']
        
        self.wd = '/'

    ###
    # UI methods
    ###
    def switch_to(self):
        global print

        self.old_print=print
        print = self.screen_print_ln

        self.output_group = displayio.Group()
        self.command_group = displayio.Group(scale=1, x=12, y=220)
        
        # Draw output window
        inner_bitmap = displayio.Bitmap(312, 200, 1)
        inner_palette = displayio.Palette(1)
        inner_palette[0] = 0x000000 
        output_grid = displayio.TileGrid(inner_bitmap, pixel_shader=inner_palette, x=4, y=4)
        self.window.append(output_grid)
        self.window.append(self.output_group)

        # Draw text input window
        inner_bitmap = displayio.Bitmap(312, 28, 1)
        inner_palette = displayio.Palette(1)
        inner_palette[0] = 0x000000 
        command_grid = displayio.TileGrid(inner_bitmap, pixel_shader=inner_palette, x=4, y=208)
        self.window.append(command_grid)
        self.window.append(self.command_group)

        command_label = label.Label(terminalio.FONT, text=self.command, color=0xFFFFFF)
        self.command_group.append(command_label)

        self.reload_lines()
        
    def switch_from(self):
        global print

        print = self.old_print
        return True

    def handle_keyboard(self, pressed):

        if pressed == '\b':
            self.command = self.command[:-1]
        elif pressed == '\n': 

            print('> '+ self.command)

            if len(self.command.strip()) > 0:
                if '=' in self.command and not '==' in self.command:
                    try:
                        exec(self.command)
                        print('')
                    except Exception as e:
                        print(str(e))
                else:
                    try:
                        result = eval(self.command)
                        if result is None:
                            result = ''
                        
                        print(str(result))
                    except Exception as e:
                        print(str(e))
            
            self.command = ''
        elif pressed == '`':
            self.command = self.command + '='
        elif pressed == '@':
            self.command = self.command + '['
        elif pressed == '~':
            self.command = self.command + ']'
        else:
            self.command = self.command + pressed

        self.command_group.pop()
        command_label = label.Label(terminalio.FONT, text=self.command, color=0xFFFFFF)
        self.command_group.append(command_label)
        gc.collect()
        time.sleep(0.03) 

    ###
    # Helper methods
    ###
    def reload_lines(self):

        for i in range(len(self.output_group)):
            self.output_group.pop()

        for i in range(len(self.screen_lines)):
            text_group = displayio.Group(scale=1, x=12, y=12 *(i + 1) )
            text_area = label.Label(terminalio.FONT, text=self.screen_lines[i], color=0xFFFFFF)
            text_group.append(text_area)
            self.output_group.append(text_group)

    def screen_print_ln(self, text):

        text = str(text)

        screen_lines_len = len(self.screen_lines)
        if screen_lines_len < self.SCREEN_BUFF_LEN:
            self.screen_lines.append(text)
            text_group = displayio.Group(scale=1, x=12, y=12 *(screen_lines_len + 1) )
            text_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF)
            text_group.append(text_area)
            self.output_group.append(text_group)
        else:
            del self.screen_lines[0]
            self.screen_lines.append(text)
            gc.collect()
            self.reload_lines()
    
    ###
    # Terminal commands
    ###
    def run(self, path):
        file = open(path, 'r')
        # file_lines = file.readlines()
        try:
            exec(file.read())
        except Exception as e:
            print(str(e))
    
    def mount(self):
        sdcard = sdcardio.SDCard(self.spi, self.sdcard_cs)
        vfs = storage.VfsFat(sdcard)
        storage.mount(vfs, "/sd")

    def ls(self, path=None):

        if path is None:
            path = self.wd

        dirs = os.listdir(path)

        for dir in dirs:
            print(dir)
    
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
    
    def pwd(self):

        print(self.wd)

    def mv(self, old, new):

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
        
        os.rename(old, new)

    def rm(self, path):

        if path.startswith('./'):
            path=self.wd+path[2:]
        elif path.startswith('/'):
            pass
        else:
            path=self.wd+path

        os.remove(path)

    def cp(self, old, new):
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

        if path.startswith('./'):
            path=self.wd+path[2:]
        elif path.startswith('/'):
            pass
        else:
            path=self.wd+path
        
        os.mkdir(path)