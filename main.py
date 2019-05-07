#!/usr/bin/env python
import RPi.GPIO as GPIO
import subprocess
import time
import os
from pyky040 import pyky040
import threading
import RPi_I2C_driver
from datetime import datetime
import re
import math


GPIO.setmode(GPIO.BCM)
GPIO.setup(26, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(16, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(20, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(21, GPIO.IN, pull_up_down=GPIO.PUD_UP)
encoder_r_count = 0
encoder_r = pyky040.Encoder(CLK=17, DT=18, SW=26)
encoder_l_count = 0
encoder_l = pyky040.Encoder(CLK=16, DT=20, SW=21)
lcd = RPi_I2C_driver.lcd()
lcd.lcd_display_string(" Loading", 2)
lcd.lcd_display_string(" Please wait...", 3)
time.sleep(3)
lcd.lcd_clear()

def vol_up_callback(rotvalue):
    global encoder_l_count
    global encoder_r_count
    if encoder_r_count < 1:
        encoder_r_count += 1
    elif encoder_r_count == 1:
        os.system("amixer -M set 'PCM' 2%+")
        encoder_r_count = 0
        encoder_l_count = 0

def vol_down_callback(rotvalue):
    global encoder_l_count
    global encoder_r_count
    if encoder_l_count < 1:
        encoder_l_count += 1
    elif encoder_l_count == 1:
        os.system("amixer -M set 'PCM' 2%-")
        encoder_l_count = 0
        encoder_r_count = 0

def vol_toggle_callback():
    os.system("amixer -M set 'PCM' toggle")

def get_vol_value():
    vol_val_p = subprocess.Popen(["amixer","-M","get","'PCM'"],stdout=subprocess.PIPE)
    while True:
        line = vol_val_p.stdout.readline()
        if "Mono:" in line:
            vol_val = re.split("\[|\]", line)[1]
        elif line == "":
            return vol_val

def iradio_ctrl(ictrl_file=""):
   iradio_p = subprocess.Popen(["omxplayer --adev alsa --vol -300 "+ictrl_file], 
    shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)


encoder_r.setup(scale_min=0, scale_max=1, step=1, inc_callback=vol_up_callback, 
            dec_callback=vol_down_callback, sw_callback=vol_toggle_callback, polling_interval=1000, sw_debounce_time=300)
encoder_l.setup(scale_min=0, scale_max=1, step=1, inc_callback=vol_up_callback, 
            dec_callback=vol_down_callback, sw_callback=vol_toggle_callback, polling_interval=1000, sw_debounce_time=300)
thread_enc_r = threading.Thread(target=encoder_r.watch)
thread_enc_l = threading.Thread(target=encoder_l.watch)

thread_enc_r.start()
thread_enc_l.start()

last_vol = get_vol_value()
bussy_counter = int()
disp_state = ""
states = ["iRadio", "FM Radio", "MP3", "Bluetooth"]
state = ""
ictrl_file = "http://live.magicfm.ro:9128/magicfm.aacp"


iradio_ctrl(ictrl_file)

while True:
    range(10000)
    vol_value = get_vol_value()
    if last_vol != vol_value:
        disp_state = "volume"
        lcd.lcd_clear()
        lcd.lcd_display_string(" Volume: "+vol_value, 3)
        last_vol = vol_value
        bussy_counter = int(time.time())+2
    if bussy_counter < int(time.time()) and disp_state != "main":
        disp_state = "main"
        lcd.lcd_clear()
        lcd.lcd_display_string_pos("iRADIO",1,1)
        lcd.lcd_display_string(" Europa FM Buc", 3)
    time.sleep(0.2)
