# SPDX-FileCopyrightText: 2018 Kattni Rembor for Adafruit Industries
#
# SPDX-License-Identifier: MIT

import rotaryio
import board
import digitalio
import analogio
import usb_hid
import time
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode
from adafruit_debouncer import Debouncer
from ControlGroup import ControlGroup

analogIns = [ board.GP26, board.GP27, board.GP28 ]

adc = [ 
    analogio.AnalogIn(analogIns[0]),
    analogio.AnalogIn(analogIns[1]),
    analogio.AnalogIn(analogIns[2])
]


    

def remapAdc(adc_value):
    return int(adc_value / 65535 * 1024)

debugPin        = board.GP12
debug           = digitalio.DigitalInOut(debugPin)
debug.direction = digitalio.Direction.INPUT
debug.pull      = digitalio.Pull.UP

tap_delay       = 1
fader_interval  = 0.01

cc = ConsumerControl(usb_hid.devices)
master_counter  = None
fader_counter   = None


def log_debug (msg):
    if not debug.value:
        print(msg)
        time.sleep(.2)


masterEnc = ControlGroup(board.GP15, board.GP14, board.GP13)

def master_loop ():
    global master_counter

    masterEnc.update()
    if masterEnc.delta_pos > 0:
        for _ in range(masterEnc.delta_pos):
            cc.send(ConsumerControlCode.VOLUME_INCREMENT)
            log_debug("Tick Volume UP")
    elif masterEnc.delta_pos < 0:
        for _ in range(-masterEnc.delta_pos):
            cc.send(ConsumerControlCode.VOLUME_DECREMENT)
            log_debug("Tick Volume Down")
    masterEnc.last_pos = masterEnc.current_pos

    masterEnc.button.update()
    if masterEnc.button.fell:
        if master_counter is None:
            master_counter = time.monotonic()
            log_debug("Push MUTE    | Counter " 
                + str(master_counter) 
                + " Time: " 
                + str(time.monotonic()))
        else:
            log_debug("Push MUTE    | Counter " 
                + str(master_counter) 
                + " Time: " 
                + str(time.monotonic()))
        cc.send(ConsumerControlCode.MUTE)
    
    if masterEnc.button.rose:
        if master_counter is None or (time.monotonic() - master_counter) <= tap_delay :
            log_debug("Release Mute | Counter " 
                + str(master_counter) 
                + " Time: " 
                + str(time.monotonic()) 
                + " Diff: " 
                + str(time.monotonic() - master_counter))
            master_counter = None
        else: 
            cc.send(ConsumerControlCode.MUTE)
            log_debug("Hold Umute   | Counter " 
                + str(master_counter) 
                + " Time: " 
                + str(time.monotonic()) 
                + " Diff: " 
                + str(time.monotonic() - master_counter))
            master_counter = None

def faders_loop():
    global fader_counter
    
    if fader_counter is None:
        fader_counter = time.monotonic()
    if (time.monotonic() - fader_counter) <= fader_interval: 
        log_debug("Fader Timer  | Time: " 
            + str(time.monotonic()) 
            + " Counter: " 
            + str(fader_counter) 
            + " Diff: " 
            + str(time.monotonic() - fader_counter))
        return
    else:
        if debug.value:
            print(str(remapAdc(adc[0].value)) 
                + '|' 
                + str(remapAdc(adc[1].value)) 
                + '|' 
                + str(remapAdc(adc[2].value)))
        fader_counter = None # 
        
        

while True:
    master_loop()
    faders_loop()
