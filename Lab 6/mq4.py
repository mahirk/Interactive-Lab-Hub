#from __future__ import print_function
#import os
#import subprocess
#from time import sleep
import board
#import numpy as np
import busio
import qwiic
from sshkeyboard import listen_keyboard

import paho.mqtt.client as mqtt
import uuid

topic = 'IDD/MVP'
# Create the I2C interface.
i2c = busio.I2C(board.SCL, board.SDA)

############################################################
def distances():       

    ToF.start_ranging()
    distance = ToF.get_distance()	 # Get the result of the measurement from the sensor
    ToF.stop_ranging()
    
    #distanceFeet = distance / 304.8 
    
    distanceInches = distance * 0.0393701
    #print("inches ", distanceInches)
    
    distanceInches = round(distanceInches, 3)
    
    
    return distanceInches

###############################################################

def listen():  
    listen_keyboard(on_press=press)
    
##################################################################
    
def press(key):
    if key == 'd':
        distance = distances()
        #print(distance)
        
    distance_lower_bar = round((distance * .9),3)
    distance_upper_bar = round((distance * 1.1),3)
    
    response = (f"Mahir measured {distance} you try must be between {distance_lower_bar} and {distance_upper_bar}")
    
    client.publish(topic, response)

##########################################################################

def on_connect(client, userdata, flags, rc):
    
    print(f"connected with result code {rc}")
    client.subscribe(topic)
    
####################################################################

def on_message(cleint, userdata, msg):
    
    # function to receive the message
    if msg.topic == topic:
        print(msg.payload.decode())
        
#######################################################################

client = mqtt.Client(str(uuid.uuid1()))
client.tls_set()
client.username_pw_set('idd', 'device@theFarm')
client.on_connect = on_connect
client.on_message = on_message

client.connect('farlab.infosci.cornell.edu', port=8883)

client.loop_start()


while True:
    
    ToF = qwiic.QwiicVL53L1X()
    if (ToF.sensor_init() == None):					 # Begin returns 0 on a good init
        print("Sensor online!\n")    
    
    listen()
     
