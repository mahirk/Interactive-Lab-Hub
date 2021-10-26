import qwiic
import time
import board
from adafruit_seesaw import seesaw, rotaryio, digitalio
import busio
import adafruit_ssd1306
from PIL import Image, ImageDraw, ImageFont
import gtts
from pydub import AudioSegment
from pydub.playback import play
from io import BytesIO
from pydub.utils import which, mediainfo
import qwiic_button
import math

font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)

# Create the I2C interface.
i2c = busio.I2C(board.SCL, board.SDA)
my_button = qwiic_button.QwiicButton()
oled = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c)

image = Image.new("1", (oled.width, oled.height))
draw = ImageDraw.Draw(image)

print("VL53L1X Qwiic Test\n")
ToF = qwiic.QwiicVL53L1X()
if (ToF.sensor_init() == None):  # Begin returns 0 on a good init
    print("Sensor online!\n")
if my_button.begin() == False:
        print("\nThe Qwiic Button isn't connected to the system. Please check your connection")

seesaw = seesaw.Seesaw(i2c, addr=0x36)

seesaw_product = (seesaw.get_version() >> 16) & 0xFFFF
print("Found product {}".format(seesaw_product))
if seesaw_product != 4991:
    print("Wrong firmware loaded?  Expected 4991")

seesaw.pin_mode(24, seesaw.INPUT_PULLUP)
button = digitalio.DigitalIO(seesaw, 24)
button_held = False

encoder = rotaryio.IncrementalEncoder(seesaw)
last_position = None

def playsound(text):
    tts = gtts.gTTS(text, lang="en")
    mp3_fp = BytesIO()
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    song = AudioSegment.from_file(mp3_fp, format="mp3")
    play(song)

def show_stop():
    draw.rectangle((0, 0, 128, 32), outline=0, fill=0)
    draw.text((0, 0), "STOP", font=font, fill=255)
    oled.image(image)
    oled.rotate(2)
    oled.show()
    my_button.LED_on(100)
    playsound("Please stop, you have passed the threshold")

def remove_stop(distanceMeasure):
    draw.rectangle((0, 0, 128, 32), outline=0, fill=0)
    draw.text((0, 0), "{} ft".format(math.floor(distanceMeasure / 12)), font=font, fill=255)
    oled.image(image)
    oled.rotate(2)
    oled.show()
    my_button.LED_off()

def get_position(position):
    return (38 + position)

while True:
    position = -encoder.position
    try:
        ToF.start_ranging()  # Write configuration bytes to initiate measurement
        time.sleep(.005)
        distance = ToF.get_distance()  # Get the result of the measurement from the sensor
        time.sleep(.005)
        ToF.stop_ranging()

        distanceInches = distance / 25.4
        distance_from_sensor = get_position(position)
        if distanceInches < distance_from_sensor:
            show_stop()
        else:
            remove_stop(distance_from_sensor)
            # print(distance_from_sensor / 12)
    except Exception as e:
        print(e)
