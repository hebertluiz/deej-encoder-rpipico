# class for controlling the display

import adafruit_ssd1306
import busio
from time import monotonic


# i2c = busio.I2C(board.GP5, board.GP4, frequency=20000)
# display = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3c)


class Display():
    channels_VU = {}
    font_height = 12
    line_height = font_height + 3
    is_inverted = False
    sleeping = False
    lastActive = monotonic()
    def __init__(
        self,
        scl, sda, 
        frequency=20000, 
        v_size=64, h_size=128, 
        i2c_address=0x3c,
        fader_banks=None,
        fader_banks_len=0):
    
        self.v_size, self.h_size = (v_size, h_size)
        self.FaderBanksVU = fader_banks
        self.fader_banks_len = fader_banks_len
        self.i2c = busio.I2C(scl, sda)
        self.screen = adafruit_ssd1306.SSD1306_I2C(h_size, v_size, self.i2c, addr=i2c_address)
        
        for vu in range(0,fader_banks_len):
            self.channels_VU[vu] = int(
                0 + (self.h_size - 0 ) * ((
                self.FaderBanksVU[vu]['Value'] - 0
                ) / (1023 - 0)))
            self.drawVU(vu)
    
    def getChanPos(self, channel_id):
        return channel_id*self.line_height
    
    def getVuPos(self, channel_id):
        return ((channel_id+1)*self.line_height)-( self.line_height - self.font_height)
        
    def clear(self):
        self.screen.invert(self.is_inverted)
        self.screen.fill(1 if self.is_inverted else 0)
    
    def show(self):
        if self.sleeping:
            self.lastActive = monotonic()
            self.screen.poweron()
        self.screen.show()

    def sleep(self):
        self.screen.poweroff()
        self.sleeping = True
        
    def invert(self):
        if self.sleeping:
            self.lastActive = monotonic()
            self.screen.poweron()
        if self.is_inverted:
            self.is_inverted = False
            self.screen.contrast(127)
            self.screen.invert(self.is_inverted)
        else: 
            self.is_inverted = True
            for vu in range(0,self.fader_banks_len):
                self.drawVU(vu)
            self.screen.contrast(127)
            self.screen.invert(self.is_inverted)


    def boot(self, text):
        self.clear()
        self.screen.text(text, 0, int(self.v_size/4), 0)
        self.show()
        
    
    def drawChannel(self, name, channel_id, enabled=False):
        if self.sleeping:
            self.lastActive = monotonic()
            self.screen.poweron()
        state = '*' if enabled else '-'
        self.screen.text(
            f'{"*" if enabled else "-"} {name}',              # Text
            0, self.getChanPos(channel_id), # Position
            0 if self.is_inverted else 1,   # Color 1 white on black and 0 black on White
            size=8 if self.font_height<=8 else int(self.font_height/8)    # Font size never less then 8
        )
        
        self.drawVU(channel_id)
    
    def drawVU(self, channel_id):
        if self.sleeping:
            self.lastActive = monotonic()
            self.screen.poweron()
        width = 3
        offset = 1
        # clear line
        self.screen.fill_rect(
            0, self.getVuPos(channel_id) - offset,
            self.h_size, width,
            color=1 if self.is_inverted else 0 
        )
        
        # draw fader bar
        self.screen.fill_rect(
            0, self.getVuPos(channel_id) - offset,
            self.channels_VU[channel_id], width,
            color=0 if self.is_inverted else 1 
        )


    def updateChannel(self, faderBank, currentPotBank, maxValue=1023):
        value = int(0 + (self.h_size - 0 ) * ((
            faderBank[currentPotBank]['Value'] - 0
            ) / (maxValue - 0)))
        self.channels_VU[currentPotBank] = value
