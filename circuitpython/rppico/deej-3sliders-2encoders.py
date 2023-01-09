import rotaryio
import board
import digitalio
import analogio
import usb_hid
import time
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode

from adafruit_debouncer import Debouncer
from ControlGroup import ControlGroup
from VirtualPotBank import VirtualPotBank

from DisplayControl import Display

analogIns = [  board.GP28, board.GP26, board.GP27]
adc = [ 
    analogio.AnalogIn(analogIns[0]),
    analogio.AnalogIn(analogIns[1]),
    analogio.AnalogIn(analogIns[2])
]

mech_switchesInputs = [
    board.GP18,     # Pin: 24 RightSide 17
    board.GP19      # Pin: 25 RightSide 16
]


## Digital ports and Encoders pins
master_clock        = board.GP15    # Pin: 20 LeftSide
master_data         = board.GP14    # Pin: 19 LeftSide
master_pushButton   = board.GP13    # Pin: 17 LeftSide

generic_clock       = board.GP9     # Pin: 12 LeftSide 
generic_data        = board.GP8     # Pin: 11 LeftSide
generic_pushButton  = board.GP7     # Pin: 10 LeftSide

debug_switch = board.GP12

## I2C port
SCL = board.GP5
SDA = board.GP4

## Master encoder config
tap_delay       = 1
master_multiplier = 1.5

## Faders Config
fader_interval  = 0.01
maxPotValue = 1023

## Virtual Potentiometers
potOldValue = 0
virtualPots= [
    'Music  ',
    'All    ',
    'System ',
    'Custom1'
]

## Screen Config
screenSleep = 300
framerate = 1/10

## Timers for periodic actions
lastDisplayUpdate = time.monotonic()
master_counter  = None
fader_counter   = None

## Switch array
mech_switches = []

def createButton(button_pin):
    button = digitalio.DigitalInOut(button_pin)
    button.direction = digitalio.Direction.INPUT
    button.pull = digitalio.Pull.UP
    return Debouncer(button, interval=0.02)

def createEncoder(clock_pin, data_pin):
    return rotaryio.IncrementalEncoder(clock_pin, data_pin)

def remapAdc(adc, max):
    adcVal = int(adc.value / 65535 * (max + 1))
    if adcVal <= 6:
        return int(adcVal/5)
    elif adcVal >= 1019:
        return 1023
    
    return adcVal

def setupDebug (debugPin):
    debug           = digitalio.DigitalInOut(debugPin)
    debug.direction = digitalio.Direction.INPUT
    debug.pull      = digitalio.Pull.UP
    return debug

debug = setupDebug(debug_switch)
masterEnc = ControlGroup(createEncoder(master_clock , master_data), createButton(master_pushButton))
currentVpot = 0

faderBank = VirtualPotBank(
    createEncoder(generic_clock, generic_data), 
    virtualPots,
    createButton(generic_pushButton)
    )

display = Display(
    SCL,
    SDA,
    i2c_address=0x3c,
    fader_banks=faderBank.Banks,
    fader_banks_len=len(virtualPots)
)


for mech_input in mech_switchesInputs:
    mech_switches.append(createButton(mech_input))



cc = ConsumerControl(usb_hid.devices)
kb = Keyboard(usb_hid.devices)


def master_loop ():
    global master_counter

    masterEnc.update()
    masterEnc.delta_pos = int(masterEnc.delta_pos * master_multiplier)
    if masterEnc.delta_pos > 0:
        for _ in range(masterEnc.delta_pos):
            cc.send(ConsumerControlCode.VOLUME_INCREMENT)
    elif masterEnc.delta_pos < 0:
        for _ in range(-masterEnc.delta_pos):
            cc.send(ConsumerControlCode.VOLUME_DECREMENT)
    masterEnc.last_pos = masterEnc.current_pos

    masterEnc.button.update()
    if masterEnc.button.fell:
        if master_counter is None:
            master_counter = time.monotonic()
        cc.send(ConsumerControlCode.MUTE)
    
    if masterEnc.button.rose:
        if master_counter is None or (time.monotonic() - master_counter) <= tap_delay :
            master_counter = None
        else: 
            cc.send(ConsumerControlCode.MUTE)
            master_counter = None

def generic_fader_loop():
    global potOldValue
    global virtualPots
    global lastDisplayUpdate
    faderBank.button.update()
    
    
    if faderBank.button.fell:
        faderBank.currentPotBank = faderBank.currentPotBank + 1
        if faderBank.currentPotBank >= len(virtualPots):
            faderBank.currentPotBank = 0
            
        display.clear()
        for bank in range(0, len(virtualPots)):
            is_enabled = True if faderBank.currentPotBank == bank else False
            display.drawChannel(virtualPots[bank], bank, is_enabled)
        display.show()

    currentValue = faderBank.updateBank(faderBank.currentPotBank)

    if currentValue > potOldValue + 10 or currentValue < potOldValue -10 :
        if time.monotonic() - lastDisplayUpdate >= framerate:
            display.updateChannel(
                faderBank.Banks,
                faderBank.currentPotBank)
            display.drawVU(faderBank.currentPotBank)
            potOldValue = faderBank.Banks[faderBank.currentPotBank]['Value']
            display.show()


    
    
    

    return faderBank.returnVirtualPotBanks()
    

def faders_loop(virtPots=''):
    global fader_counter
    global currentVpot
    
    if virtPots != '':
        virtPots = f'|{virtPots}'
    
    if fader_counter is None:
        fader_counter = time.monotonic()
    if (time.monotonic() - fader_counter) <= fader_interval: 
        adc0 = f'{remapAdc(adc[0], maxPotValue):04}' 
        adc1 = f'{remapAdc(adc[1], maxPotValue):04}' 
        adc2 = f'{remapAdc(adc[2], maxPotValue):04}' 
        return
    else:
        if debug.value:
            print(
                  f'{remapAdc(adc[0], maxPotValue)}' 
                + '|' 
                + f'{remapAdc(adc[1], maxPotValue)}' 
                + '|' 
                + f'{remapAdc(adc[2], maxPotValue)}'
                +  virtPots
            )
        fader_counter = None
        
def check_mech_buttons():
    for button in range(0, len(mech_switches)):
        mech_switches[button].update()
        if mech_switches[button].fell:
            if button == 0: kb.send(Keycode.F13)
            if button == 1: kb.send(Keycode.F14)
    

display.boot("Initializing Deej")
time.sleep(0.8)
 

display.clear()


for bank in range(0, len(virtualPots)):
    is_enabled = True if faderBank.currentPotBank == bank else False
    display.drawChannel(virtualPots[bank], bank, is_enabled)
    
display.show()

while True:
    
    if (time.monotonic() - display.lastActive ) >= screenSleep :
        display.sleep()
        
    
    check_mech_buttons()
    master_loop()
    faders_loop(generic_fader_loop())



