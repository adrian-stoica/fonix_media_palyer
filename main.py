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

iradio_p = None
vol_r_count = 0
vol_l_count = 0
tune_l_callback_count = 0
tune_r_callback_count = 0
not_connected_count = 0

#Define the functions that are going to be used in the main loop

def vol_callback(rotvalue):
    global vol_r_count
    global vol_l_count
    global disp_state
    if rotvalue == 1:
        if vol_r_count < 1:
            vol_r_count += 1
        elif vol_r_count == 1:
            os.system("amixer -M set 'PCM' 2%+")
            vol_l_count = 0
    elif rotvalue == 0:
        if vol_l_count < 1:
            vol_l_count += 1
        elif vol_l_count == 1:
            os.system("amixer -M set 'PCM' 2%-")
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
    global iradio_p
    global not_connected_count
    if not os.system('pidof /usr/bin/omxplayer.bin'):
        os.system("kill -9 $(pidof /usr/bin/omxplayer.bin) > /dev/null 2>&1")
    p_location = plst.tlocation(track_no)
    plen = plst.lenght()
    track_name = plst.tname(track_no)
    iradio_p = subprocess.Popen(["omxplayer --adev alsa --vol -300 "+p_location], shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    not_connected_count = 0

def iradio_check():
    global not_connected_count
    while True:
        if os.system('pidof /usr/bin/omxplayer.bin'):
            not_connected_count += 1
        if not_connected_count >= 10:
            iradio_ctrl()
            not_connected_count = 0
        time.sleep(0.1)

def tune_callback(rotvalue):
    global track_no
    global tune_l_callback_count
    global tune_r_callback_count
    plen = plst.lenght()
    if rotvalue == 1 and track_no < int(plen-1):
        if tune_r_callback_count < 4:
            tune_r_callback_count += 1
        elif tune_r_callback_count == 4:
            tune_l_callback_count = 0
            tune_r_callback_count = 0
            track_no += 1
            iradio_ctrl()
            time.sleep(0.1)
    elif rotvalue == 0 and track_no > 0:
        if tune_l_callback_count < 4:
            tune_l_callback_count += 1
        elif tune_l_callback_count == 4:
            track_no -= 1
            tune_l_callback_count = 0
            tune_r_callback_count = 0
            iradio_ctrl()
            time.sleep(0.1)

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
#Start rotary encoders threads
encoder_r.setup(scale_min=0, scale_max=1, step=1, inc_callback=vol_callback, 
            dec_callback=vol_callback, sw_callback=vol_toggle_callback, polling_interval=2000, sw_debounce_time=500)
encoder_l.setup(scale_min=0, scale_max=1, step=1, inc_callback=tune_callback, 
            dec_callback=tune_callback, sw_callback=vol_toggle_callback, polling_interval=2000, sw_debounce_time=500)
thread_enc_r = threading.Thread(target=encoder_r.watch)
thread_enc_l = threading.Thread(target=encoder_l.watch)
radio_reconnect = threading.Thread(target=iradio_check)

thread_enc_r.start()
thread_enc_l.start()
radio_reconnect.start()
bussy_counter = int()
disp_state = ""
stored_clock = clock()
states = []
mode, track_no = state_read()
stored_track_no = track_no
stored_vol_value = get_vol_value()
main_display_state = 0
plst = playListParser(work_dir+"playlists/radio.xspf")

#start the radio with stored station
iradio_ctrl()

#The main loop
while True:
    #Update clock on display
    if  stored_clock != str(clock()) and bussy_counter < int(time.time()):
        track_name = plst.tname(track_no)
        stored_clock = str(clock())
        lcd.lcd_display_string_pos(stored_clock,1,7)
    #Show stations selection on display
    if stored_track_no != track_no:
        bussy_counter = int(time.time())+3
        lcd.lcd_clear()
        lcd.lcd_display_string_pos("Channel: "+str(track_no+1)+"/"+str(plst.lenght()),2,0)
        lcd.lcd_display_string_pos(str(plst.tname(track_no)),3,0)
        main_display_state = 0
        stored_track_no = track_no
    #Display volume change
    if stored_vol_value != get_vol_value():
        bussy_counter = int(time.time())+3
        lcd.lcd_clear()
        vol_value = get_vol_value()
        lcd.lcd_display_string(" Volume: "+vol_value, 3)
        main_display_state = 0
        stored_vol_value = vol_value
    #Display the main screen
    if main_display_state == 0 and bussy_counter < int(time.time()):
        track_name = plst.tname(track_no)
        lcd.lcd_clear()
        main_display_state = 1
        lcd.lcd_display_string_pos(stored_clock,1,7)
        lcd.lcd_display_string_pos(track_name,3,0)
        if stored_vol_value == '0%':
            lcd.lcd_display_string_pos("MUTE",4,16)
        elif stored_vol_value != '0%':
            lcd.lcd_display_string_pos("    ",4,16)
        stored_clock = str(clock())
        state_write("iradio", track_no)
    time.sleep(0.05)
#End of the main loop