#!/usr/bin/env python
work_dir = "/opt/fonix_media_palyer/"
import sys
sys.path.insert(0, work_dir+'modules')
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
from radiotools import playListParser


GPIO.setmode(GPIO.BCM)
GPIO.setup(26, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(16, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(20, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(21, GPIO.IN, pull_up_down=GPIO.PUD_UP)
iradio_p = ""
vol_r_count = 0
vol_l_count = 0
tune_l_callback_count = 0
tune_r_callback_count = 0
encoder_r = pyky040.Encoder(CLK=17, DT=18, SW=26)
encoder_l = pyky040.Encoder(CLK=16, DT=20, SW=21)
lcd = RPi_I2C_driver.lcd()
lcd.lcd_display_string(" Loading", 2)
lcd.lcd_display_string(" Please wait...", 3)
time.sleep(3)
lcd.lcd_clear()

def vol_callback(rotvalue):
    global vol_r_count
    global vol_l_count
    if rotvalue == 1:
        if vol_r_count < 1:
            vol_r_count += 1
        elif vol_r_count == 1:
            os.system("amixer -M set 'PCM' 4%+")
            vol_r_count = 0
            vol_l_count = 0
    elif rotvalue == 0:
        if vol_l_count < 1:
            vol_l_count += 1
        elif vol_l_count == 1:
            os.system("amixer -M set 'PCM' 4%-")
            vol_r_count = 0
            vol_l_count = 0

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
    global iradio_p
    pool = iradio_p.poll()
    if pool == None:
        iradio_p.stdin.write('q\n'.encode())
        iradio_p = subprocess.Popen(["omxplayer --adev alsa --vol -300 "+ictrl_file], shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    else:
        iradio_p = subprocess.Popen(["omxplayer --adev alsa --vol -300 "+ictrl_file], shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)

def display_station():
    p_location = plst.tlocation(track_no)
    iradio_ctrl(p_location)
    track_name = plst.tname(track_no)
    lcd.lcd_clear()
    lcd.lcd_display_string("Channel: "+str(track_no+1), 2)
    lcd.lcd_display_string(track_name, 3)

def tune_callback(rotvalue):
    global track_no
    global tune_l_callback_count
    global tune_r_callback_count
    plen = plst.lenght()
    bussy_counter = int(time.time())+2
    if rotvalue == 1 and track_no < int(plen-1):
        if tune_r_callback_count < 3:
            tune_r_callback_count += 1
        elif tune_r_callback_count == 3:
            track_no += 1
            display_station()
            tune_l_callback_count = 0
            tune_r_callback_count = 0
    elif rotvalue == 0 and track_no > 0:
        if tune_l_callback_count < 3:
            tune_l_callback_count += 1
        elif tune_l_callback_count == 3:
            track_no -= 1
            display_station()
            tune_l_callback_count = 0
            tune_r_callback_count = 0

def clock():
    clock_get = datetime.now()
    clock_str = str(clock_get.strftime("%H:%M:%S"))
    return clock_str

def state_read():
    f = open(work_dir+"l_state")
    f_list = (f.read()).split(";")
    mode = str(f_list[0])
    track = int(f_list[1])
    f.close()
    return mode, track

encoder_r.setup(scale_min=0, scale_max=1, step=1, inc_callback=vol_callback, 
            dec_callback=vol_callback, sw_callback=vol_toggle_callback, polling_interval=1000, sw_debounce_time=300)
encoder_l.setup(scale_min=0, scale_max=1, step=1, inc_callback=tune_callback, 
            dec_callback=tune_callback, sw_callback=vol_toggle_callback, polling_interval=1000, sw_debounce_time=300)
thread_enc_r = threading.Thread(target=encoder_r.watch)
thread_enc_l = threading.Thread(target=encoder_l.watch)

thread_enc_r.start()
thread_enc_l.start()

last_vol = get_vol_value()
bussy_counter = int()
disp_state = ""
clock_set = ""
states = []
mode, track_no = state_read()

plst = playListParser(work_dir+"playlists/radio.xspf")
p_location = plst.tlocation(track_no)

iradio_ctrl(p_location)

while True:
    range(10000)
# Display the volume value
    vol_value = get_vol_value()
    if last_vol != vol_value:
        disp_state = "volume"
        lcd.lcd_clear()
        lcd.lcd_display_string(" Volume: "+vol_value, 3)
        last_vol = vol_value
        bussy_counter = int(time.time())+2
# Back to display main screen
    if bussy_counter < int(time.time()) and disp_state != "main":
        disp_state = "main"
        clock_set = str(clock())
        track_name = plst.tname(track_no)
        lcd.lcd_clear()
        lcd.lcd_display_string_pos(clock_set,1,6)
        lcd.lcd_display_string(track_name, 3)
# Update clock on display
    elif disp_state == "main" and str(clock()) != clock_set and bussy_counter < int(time.time()):
        clock_set = str(clock())
        lcd.lcd_display_string_pos(clock_set,1,6)
        pass
    time.sleep(0.1)
