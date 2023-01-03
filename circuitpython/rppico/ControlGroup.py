import rotaryio
import board
import digitalio
from adafruit_debouncer import Debouncer


class ControlGroup:
    virtualPotMin=0
    virtualPotMax=1023
    virtualPot = virtualPotMax/2

    pinCLK = None
    pinDT  = None
    pinBT  = None

    delta_pos   = 0
    current_pos = 0
    last_pos    = 0

    def __init__(self, pinCLK, pinDT, pinBT):
        self.enc = rotaryio.IncrementalEncoder(pinCLK, pinDT)
        self.last_pos = self.enc.position
        self.current_pos = None
        self.delta_pos = 0
        self.update()

        self.b_input = digitalio.DigitalInOut(pinBT)
        self.b_input.direction = digitalio.Direction.INPUT
        self.b_input.pull = digitalio.Pull.UP
        self.button = Debouncer(self.b_input, interval=0.05)
        self.button.update()

    def update(self):
        self.current_pos = self.enc.position
        self.delta_pos = self.current_pos - self.last_pos

    def virtualPotTickUp(self):
        if self.virtualPot < self.virtualPotMax:
            self.virtualPot = self.virtualPot + 1
        return self.virtualPot
    
    def virtualPotTickDown(self):
        if self.virtualPot > self.virtualPotMin:
            self.virtualPot = self.virtualPot - 1
        return self.virtualPot

    def returnSerial(self):
        return self.virtualPot
