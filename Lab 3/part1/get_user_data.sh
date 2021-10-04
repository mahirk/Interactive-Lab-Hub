#!/bin/bash
python3 speak.py "Hello! Please tell me how many pets you have? If it is more than 9, please say it in part. For example for 11, say one one"
arecord -D hw:3,0 -f cd -c1 -r 48000 -d 5 -t wav recorded_mono.wav
python3 pets.py recorded_mono.wav