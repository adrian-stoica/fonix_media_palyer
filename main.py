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
encoder_r = pyky040.Encoder(CLK=17, DT=18, SW=26)
encoder_l = pyky040.Encoder(CLK=16, DT=20, SW=21)
lcd = RPi_I2C_driver.lcd()
lcd.lcd_clear()

iradio_p = ""
vol_r_count = 0
vol_l_count = 0
tune_l_callback_count = 0
tune_r_callback_count = 0

def vol_callback(rotvalue):
    global vol_r_count
    global vol_l_count
    global disp_state
    if rotvalue == 1:
        disp_state = "volume"
        if vol_r_count < 1:
            vol_r_count += 1
        elif vol_r_count == 1:
            os.system("amixer -M set 'PCM' 6%+")
            vol_l_count = 0
    elif rotvalue == 0:
        disp_state = "volume"
        if vol_l_count < 1:
            vol_l_count += 1
        elif vol_l_count == 1:
            os.system("amixer -M set 'PCM' 6%-")
            vol_r_count = 0

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

def iradio_ctrl():
    os.system("kill -9 $(pidof /usr/bin/omxplayer.bin) > /dev/null 2>&1")
    p_location = plst.tlocation(track_no)
    plen = plst.lenght()
    track_name = plst.tname(track_no)
    iradio_p = subprocess.Popen(["omxplayer --adev alsa --vol -300 "+p_location], shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)

def tune_callback(rotvalue):
    global track_no
    global tune_l_callback_count
    global tune_r_callback_count
    plen = plst.lenght()
    if rotvalue == 1 and track_no < int(plen-1):
        if tune_r_callback_count < 2:
            tune_r_callback_count += 1
        elif tune_r_callback_count == 2:
            track_no += 1
            state_write("iradio", track_no)
            iradio_ctrl()
            tune_l_callback_count = 0
            tune_r_callback_count = 0

    elif rotvalue == 0 and track_no > 0:
        if tune_l_callback_count < 2:
            tune_l_callback_count += 1
        elif tune_l_callback_count == 2:
            track_no -= 1
            state_write("iradio", track_no)
            iradio_ctrl()
            tune_l_callback_count = 0
            tune_r_callback_count = 0

def clock():
    clock_get = datetime.now()
    clock_str = str(clock_get.strftime("%H:%M"))
    return clock_str

def state_read():
    f = open(work_dir+"l_state")
    f_list = (f.read()).split(";")
    mode = str(f_list[0])
    track = int(f_list[1])
    f.close()
    return mode, track

def state_write(mode, track):
    f = open(work_dir+"l_state", "w")
    f.write(mode+";"+str(track))
    f.close()

encoder_r.setup(scale_min=0, scale_max=1, step=1, inc_callback=vol_callback, 
            dec_callback=vol_callback, sw_callback=vol_toggle_callback, polling_interval=1000, sw_debounce_time=300)
encoder_l.setup(scale_min=0, scale_max=1, step=1, inc_callback=tune_callback, 
            dec_callback=tune_callback, sw_callback=vol_toggle_callback, polling_interval=1000, sw_debounce_time=300)
thread_enc_r = threading.Thread(target=encoder_r.watch)
thread_enc_l = threading.Thread(target=encoder_l.watch)

thread_enc_r.start()
thread_enc_l.start()
bussy_counter = int()
disp_state = ""
stored_clock = clock()
states = []
mode, track_no = state_read()
stored_track_no = track_no
stored_vol_value = get_vol_value()
main_display_state = 1
plst = playListParser(work_dir+"playlists/radio.xspf")

#start the radio with stored station
iradio_ctrl()
main_display("main")

while True:
    time.sleep(0.001)
    if  stored_clock != str(clock()):
        track_name = plst.tname(track_no)
        main_display_state = 1
        lcd.lcd_clear()
        lcd.lcd_display_string_pos(stored_clock,1,7)
        lcd.lcd_display_string_pos("Channel: "+str(track_no+1)+"/"+str(plst.lenght()),3,0)
        lcd.lcd_display_string_pos(track_name,4,0)
        #lcd.lcd_display_string_pos(" ",4,0)
        stored_clock = str(clock())
    elif stored_track_no != track_no:
        track_name = plst.tname(track_no)
        lcd.lcd_clear()
        lcd.lcd_display_string_pos("Channel: "+str(track_no+1)+"/"+str(plst.lenght()),2,0)
        lcd.lcd_display_string_pos(track_name,3,0)
        bussy_counter = int(time.time())+2
        main_display_state = 0
        stored_track_no = track_no
    elif stored_vol_value != get_vol_value():
        vol_value = get_vol_value()
        lcd.lcd_clear()
        lcd.lcd_display_string(" Volume: "+vol_value, 3)
        bussy_counter = int(time.time())+2
        main_display_state = 0
        stored_vol_value = vol_value
    elif main_display_state == 0 and bussy_counter < int(time.time()):
        track_name = plst.tname(track_no)
        main_display_state = 1
        lcd.lcd_clear()
        lcd.lcd_display_string_pos(stored_clock,1,7)
        lcd.lcd_display_string_pos("Channel: "+str(track_no+1)+"/"+str(plst.lenght()),3,0)
        lcd.lcd_display_string_pos(track_name,4,0)
        #lcd.lcd_display_string_pos(" ",4,0)
        stored_clock = str(clock())