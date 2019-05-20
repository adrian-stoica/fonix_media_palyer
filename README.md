# FONIX Media Player

Audio media player based on Raspberry Pi 3B+, using OMXPlayer, 1604 i2c lcd, and two rotary encoders.

## Installation

* First, 'git' and 'OMXPlayer' needs to be installed on your Raspberry Pi

`$ sudo apt-get install git`

`$ sudo apt-get install omxplayer`

* Clone this project to `/opt` folder.

`$ cd /opt`

`$ sudo git clone https://github.com/adrian-stoica/fonix_media_palyer.git`

## Note

For the moment only internet radio is working, and only with the stations declared 'playlists/radio.xspf'.

### To be done

* Web management interface;
* Bluetooth receiver mode;
* MP3 player mode;
