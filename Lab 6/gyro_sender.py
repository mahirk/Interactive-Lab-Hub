import paho.mqtt.client as mqtt
import uuid
import board
import busio
import adafruit_mpu6050
import time
topic = 'IDD/gyro/reads'

##########################################################################

def on_connect(client, userdata, flags, rc):
	print(f"connected with result code {rc}")
	client.subscribe(topic)


####################################################################

def on_message(cleint, userdata, msg):
	# function to receive the message
	if msg.topic == topic:
		acceleration = tuple(map(float, msg.payload.decode().split(',')))
		print(acceleration)


#######################################################################

i2c = busio.I2C(board.SCL, board.SDA)
mpu = adafruit_mpu6050.MPU6050(i2c)

client = mqtt.Client(str(uuid.uuid1()))
client.tls_set()
client.username_pw_set('idd', 'device@theFarm')
client.on_connect = on_connect
client.on_message = on_message

client.connect('farlab.infosci.cornell.edu', port=8883)

client.loop_start()

while True:
	x,y,z = mpu.acceleration
	client.publish(topic, f"{x},{y},{z}")
	time.sleep(0.2)
