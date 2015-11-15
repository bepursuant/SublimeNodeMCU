# Sublime Node MCU Uploader

A Sublime3 plugin written in Python3 that allows you to upload the current file (usually some lua code, ex init.lua) to a NodeMCU (ESP8266) microcontroller by simply pressing the F7 button.
This is almost entirely based on the original work posted on the esp8266.com forums by Markus Gritschat (http://www.esp8266.com/viewtopic.php?f=22&t=1026). I downloaded the script, but I was determined to make it work with Python3 and overall do a good refactoring. It has worked well for me, submit an issue if you have any problems installing or using it.

# How it works (under the hood)
This script takes a few steps to upload your file...

1. Establish a Serial Connection with the NodeMCU based on the port set in the header
2. Sends a small shell script to the NodeMCU which it immediately runs. This script receives serial data on the COM port and writes it to the file on the NodeMCU. I'm not sure if it could be done differently, but I found this method pretty clever, and it works.
3. Reads the file into a buffer and chunks it over the COM port to the NodeMCU, checking for an ACK every chunk_size bytes
4. And, if enabled, sends a command to the Node MCU to run that file

# Example Console Output
```
[SublimeNodeMCU] Uploading...
Opening serial port COM4:9600...ok!
Reset...ok!
Sending receive script to NodeMCU...ok!
Reading E:\home\kevin\Documents\GitHub\GarageNodeMCU\GarageNodeMCU.lua into memory...ok!
Sending... 13 % 27 % 40 % 54 % 68 % 81 % 95 % 100 %
ok!
Reset...ok!
Running GarageNodeMCU.lua... > dofile("GarageNodeMCU.lua")

Program Start

> [Finished in 10.4s]
```

# Installation

1. Clone this project into `%APPDATA%\Sublime Text 3\Packages\User`. Rename folder to "SublimeNodeMCU" if necessary. Full file path to the sublime-build file should be `%APPDATA%\Sublime Text 3\Packages\User\SublimeNodeMCU\SublimeNodeMCU.sublime-build`.
2. Adjust the settings at the top of SublimeNodeMCU.py to match your environment. Mainly, the COM port variable.
3. Within Sublime Text 3, click `Tools >> Build System >> SublimeNodeMCU`.
4. Open a lua file and press F7. You will see the console output, and if everything is workign, something similar to the output above.
