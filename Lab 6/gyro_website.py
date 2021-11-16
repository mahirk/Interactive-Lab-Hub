import paho.mqtt.client as mqtt
import uuid
import sys
import base64
import ssl
from io import BytesIO
from flask_mqtt import Mqtt
from flask import Flask, Response,render_template
from flask_socketio import SocketIO, send, emit
import signal
import socket

app = Flask(__name__)
app.config['MQTT_BROKER_URL'] = 'farlab.infosci.cornell.edu'
app.config['MQTT_USERNAME'] = 'idd'
app.config['MQTT_PASSWORD'] = 'device@theFarm'
app.config['MQTT_BROKER_PORT'] = 8883
app.config['MQTT_TLS_ENABLED'] = True
app.config['MQTT_TLS_INSECURE'] = True
app.config['MQTT_KEEPALIVE'] = 1
app.config['MQTT_TLS_CA_CERTS'] = '/etc/ssl/certs/ca-certificates.crt'
app.config['MQTT_TLS_VERSION'] = ssl.PROTOCOL_TLS

mqtt = Mqtt(app)
socketio = SocketIO(app)

hostname = socket.gethostname()

@app.route("/")
def hello():
    return render_template('index.html', hostname=hostname)

# the # wildcard means we subscribe to all subtopics of IDD
topic = 'IDD/gyro/reads'

@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    mqtt.subscribe(topic)
    print(f"connected with result code {rc}")

@mqtt.on_message()
def handle_message(client, userdata, message):
    acceleration = tuple(map(float, message.payload.decode().split(',')))
    socketio.emit('pong-gps', acceleration)


def signal_handler(sig, frame):
    print('Closing Gracefully')
    sys.exit(0)

@socketio.on('connect')
def test_connect():
    print('connected')
    socketio.emit('after connect',  {'data':'Lets dance'})

signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5000)
