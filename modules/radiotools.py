#!/usr/bin/env python
import sys
sys.path.insert(0,'.')
import xmltodict
import RPi_I2C_driver
import time

class playListParser:
  def __init__(self, playlist, trackNo=''):
    '''
    XSPF playlist parser.
    "playlist" variable expects the location of playlist file as string.
    "cmd" variable expects one of the following commands:
    playListLen = total number of tracks
    playListGetName = get the name of the track
    playListGetLocation = get the location of track file
    "trackNo" variable expects the track no as integer
    '''
    self.f = open(playlist, "rb")
    self.d = xmltodict.parse(self.f)

  def lenght(self):
    playlistlen = len(self.d["playlist"]["trackList"]["track"])
    return playlistlen
  def tname(self, track_no):
    if track_no < self.lenght():
      trackname = str(self.d["playlist"]["trackList"]["track"][track_no]["title"])
      return trackname
    else:
      return str("The track no. is out of range")
  def tlocation(self, track_no):
    if track_no < self.lenght():
      tracklocation = str(self.d["playlist"]["trackList"]["track"][track_no]["location"])
      return tracklocation
    else:
      return str("The track no. is out of range")

class Display:
  def __init__(self):
    '''
    Class for interacting with 1604 LCD Display.
    '''
    self.lcd = RPi_I2C_driver.lcd()
