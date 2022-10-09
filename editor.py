import time
import gc

from adafruit_display_text import label
import terminalio
import displayio

class Editor:

    def __init__(self, window, spi, sdcard_cs):
        self.window = window
        self.spi = spi
        self.sdcard_cs = sdcard_cs

        self.status_group = None
        self.output_group = None
        
        self.old_print = None

        self.SCREEN_BUFF_LEN = 17
        self.screen_lines = ['']

        self.file_lines = ['']
        self.current_row = 0
        self.current_col = 0
        self.offset = 0
        
        self.file_path = '** New File **'
        self.file = None
        self.read_only = False
        self.changed = False

    ###
    # UI methods
    ###
    def switch_to(self):
        global print

        self.old_print=print
        print = self.screen_print_ln

        self.status_group = displayio.Group(scale=1, x=12, y=10)
        self.output_group = displayio.Group()

        # Draw status bar
        inner_bitmap = displayio.Bitmap(312, 20, 1)
        inner_palette = displayio.Palette(1)
        inner_palette[0] = 0x00FF
        status_grid = displayio.TileGrid(inner_bitmap, pixel_shader=inner_palette, x=40, y=20)
        self.window.append(status_grid)
        self.window.append(self.status_group)

        status_label = label.Label(terminalio.FONT, text=self.file_path, color=0xFFFFFF)
        self.status_group.append(status_label)
        
        # Draw output window
        inner_bitmap = displayio.Bitmap(312, 210, 1)
        inner_palette = displayio.Palette(1)
        inner_palette[0] = 0x000000 
        output_grid = displayio.TileGrid(inner_bitmap, pixel_shader=inner_palette, x=4, y=25)
        self.window.append(output_grid)
        self.window.append(self.output_group)

        updated_label = label.Label(terminalio.FONT, text='', color=0xFFFFFF)
        self.output_group.append(updated_label)


        self.reload_lines()
        
    def switch_from(self):
        global print

        print = self.old_print

        if not self.read_only and self.changed:
            if self.file is None:
                # TODO: prompt for file name
                if self.file_path == '** New File **':
                    self.file_path = '/sd/temp.txt'
                try:
                    self.file = open(self.file_path, 'w')
                except Exception as e:
                    self.file_path = 'Error: ' + str(e)
                    self.update_status()
                    return False
            try:
                for line in self.file_lines:
                    self.file.write(line)
            except Exception as e:
                    self.file_path = 'Error: ' + str(e)
                    self.update_status()
                    return False
        self.file.close()
        self.file = None
        return True


    def handle_keyboard(self, pressed):

        if not self.changed:
            self.changed = True

        if pressed == '\b':
            self.screen_lines[self.current_row] = self.screen_lines[:-1]
        # elif pressed == '\n':             
        #     self.command = ''
        # elif pressed == '`':
        #     self.command = self.command + '='
        # elif pressed == '@':
        #     self.command = self.command + '['
        # elif pressed == '~':
        #     self.command = self.command + ']'
        else:
            self.screen_lines[self.current_row]+=pressed

        text_group = displayio.Group(scale=1, x=12, y=12 *(self.current_row + 1) + 20)
        updated_label = label.Label(terminalio.FONT, text=self.screen_lines[self.current_row], color=0xFFFFFF)
        text_group.append(updated_label)
        self.output_group[self.current_row] = text_group
        self.file_lines[self.offset + self.current_row] = self.screen_lines[self.current_row]
        gc.collect()
        # time.sleep(0.03) 
        pass

    ###
    # Helper methods
    ###
    def reload_lines(self):

        for i in range(len(self.output_group)):
            self.output_group.pop()

        for i in range(len(self.screen_lines)):
            text_group = displayio.Group(scale=1, x=12, y=12 *(i + 1) + 20)
            text_area = label.Label(terminalio.FONT, text=self.screen_lines[i], color=0xFFFFFF)
            text_group.append(text_area)
            self.output_group.append(text_group)

    def screen_print_ln(self, text):
        text = str(text)

        screen_lines_len = len(self.screen_lines)
        if screen_lines_len < self.SCREEN_BUFF_LEN:
            self.screen_lines.append(text)
            text_group = displayio.Group(scale=1, x=12, y=12 *(screen_lines_len + 1) + 20)
            text_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF)
            text_group.append(text_area)
            self.output_group.append(text_group)
        else:
            del self.screen_lines[0]
            self.screen_lines.append(text)
            gc.collect()
            self.reload_lines()
    
    def update_status(self):
        status_label = label.Label(terminalio.FONT, text=self.file_path, color=0xFFFFFF)
        self.status_group[0] = status_label

    ###
    # Terminal commands
    ###
    def load(self, file_path):
        
        try:
            self.file = open(file_path, 'w')
            self.file_path = file_path
        except:
            self.file = open(file_path, 'r')
            self.read_only = True
            self.file_path = 'READ ONLY: '+ file_path
            
        self.file_lines = self.file.readlines()
        
        self.current_row = 0
        self.screen_lines = self.file_lines[0:self.SCREEN_BUFF_LEN]
    
    def new(self):

        self.screen_lines = ['']
        self.file_lines = ['']
        self.current_row = 0
        self.current_col = 0
        self.offset = 0
        
        self.file_path = '** New File **'
        self.file = None
        self.read_only = False
        self.changed = False

        gc.collect()