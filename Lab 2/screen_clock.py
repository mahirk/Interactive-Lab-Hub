import time
import subprocess
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789
import geocoder
import requests
import datetime

imageMap = {}

imagesUrl = "https://openweathermap.org/img/wn/{}.png"

def get_time_from_epoch(val):
    timestamp = datetime.datetime.fromtimestamp(val)
    return str(timestamp.strftime("%H:%M"))

def load_weather_data():
    g = geocoder.ip('me')
    latitude = str(g.latlng[0])
    longitude = str(g.latlng[1])

    weatherUrl = "https://api.openweathermap.org/data/2.5/onecall"

    querystring = {
        "lat":latitude,
        "lon":longitude,
        "exclude":"hourly,minutely",
        "appid":"33a1154b742cf3f8f1a8e4ecd4341183"
    }

    headers = {
        'cache-control': "no-cache",
    }

    response = requests.request("GET", weatherUrl, headers=headers, params=querystring)
    return response.json()

def convert_kelvin_to_farenheight(kelvin):
    d_f = (kelvin - 273.15) * 9/5 + 32
    return "{} °F".format(d_f)

def get_image_item_for_display(key):
    imagepng = "{}.png".format(key)
    if imagepng not in imageMap:
        imageMap[imagepng] = requests.get(imagesUrl.format(key), stream=True).raw
    return Image.open(imageMap[imagepng])


weatherData = load_weather_data()

# Configuration for CS and DC pins (these are FeatherWing defaults on M0/M4):
cs_pin = digitalio.DigitalInOut(board.CE0)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = None

# Config for display baudrate (default max is 24mhz):
BAUDRATE = 64000000

# Setup SPI bus using hardware SPI:
spi = board.SPI()

# Create the ST7789 display:
disp = st7789.ST7789(
    spi,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=BAUDRATE,
    width=135,
    height=240,
    x_offset=53,
    y_offset=40,
)

# Create blank image for drawing.
# Make sure to create image with mode 'RGB' for full color.
height = disp.width  # we swap height/width to rotate it to landscape!
width = disp.height
image = Image.new("RGB", (width, height))
rotation = 90

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image.
draw.rectangle((0, 0, width, height), outline=0, fill=(0, 0, 0))
disp.image(image, rotation)
# Draw some shapes.
# First define some constants to allow easy resizing of shapes.
padding = -2
top = padding
bottom = height - padding
# Move left to right keeping track of the current x position for drawing shapes.
x = 0

# Alternatively load a TTF font.  Make sure the .ttf font file is in the
# same directory as the python script!
# Some other nice fonts to try: http://www.dafont.com/bitmap.php
font = ImageFont.truetype("roboto/Roboto-Regular.ttf", 18)
timeSize = 30
fontTime = ImageFont.truetype("roboto/Roboto-Regular.ttf", timeSize)

# Turn on the backlight
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True

sunrise_in_epoch = weatherData['current']['sunrise']
sunrise_str = "Sunrise: " + get_time_from_epoch(sunrise_in_epoch)

sunset_in_epoch = weatherData['current']['sunset']
sunset_str = "Sunset: " + get_time_from_epoch(sunset_in_epoch)

print(sunrise_str)
print(sunset_str)

dateValue = "Date: " + time.strftime("%m/%d/%Y")

while True:
    # Draw a black filled box to clear the image.
    draw.rectangle((0, 0, width, height), outline=0, fill=0)
    y = top
    #TODO: Lab 2 part D work should be filled in here. You should be able to look in cli_clock.py and stats.py
    timeValue = time.strftime("%H:%M:%S")

    draw.text((x, y), dateValue, font=font, fill="#FFFFFF")
    y += font.getsize(dateValue)[1] + 14
    draw.text((x, y), timeValue, font=fontTime, fill="#FFFFFF")
    y += font.getsize(timeValue)[1] + 14
    draw.text((x, y), sunrise_str, font=font, fill="#FFFFFF")
    y += font.getsize(sunrise_str)[1] + 14
    draw.text((x, y), sunset_str, font=font, fill="#FFFFFF")

    # Display image.
    disp.image(image, rotation)
    disp.image(get_image_item_for_display(weatherData['current']['weather'][0]['icon']))
    time.sleep(1)
