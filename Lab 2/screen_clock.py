import time
import subprocess
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789
import geocoder
import requests
import datetime

tweleve_hour_format = "%I:%M %p"

imageMap = {}

twilight_color = (75,0,130)
morning_color = (255, 249, 121)
afternoon_color = (229, 222, 68)
evening_color = (239, 129, 14)
night_color = (5, 55, 82)

imagesUrl = "https://openweathermap.org/img/wn/{}.png"

def get_time_from_epoch(val, fmt = "%H"):
    timestamp = datetime.datetime.fromtimestamp(val)
    return timestamp.strftime(fmt)

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
    return "{:.1f} °F".format(d_f)

def get_image_item_for_display(key):
    imagepng = "{}.png".format(key)
    if imagepng not in imageMap:
        rawPngImage = requests.get(imagesUrl.format(key), stream=True).raw
        png = Image.open(rawPngImage)
        png.load() # required for png.split()
        background = Image.new("RGB", png.size, (0,0,0))
        background.paste(png, mask=png.split()[3]) # 3 is the alpha channel
        imageMap[imagepng] = background.rotate(90)
    return imageMap[imagepng]


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
height = disp.width #135 # we swap height/width to rotate it to landscape!
width = disp.height #240
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
fontTime = ImageFont.truetype("roboto/Roboto-Regular.ttf", 35)
fontWeather = ImageFont.truetype("roboto/Roboto-Regular.ttf", 21)

# Turn on the backlight
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True

# Turn on the buttons
buttonA = digitalio.DigitalInOut(board.D23)
buttonB = digitalio.DigitalInOut(board.D24)
buttonA.switch_to_input()
buttonB.switch_to_input()


currentWeatherData = weatherData['current']
sunrise_in_epoch = currentWeatherData['sunrise']
sunset_in_epoch = currentWeatherData['sunset']
sunrise_hr = float(get_time_from_epoch(sunrise_in_epoch))
sunset_hr = float(get_time_from_epoch(sunset_in_epoch))

dateValue = "Date: {}".format(time.strftime("%m/%d/%Y"))
currentTemp = convert_kelvin_to_farenheight(currentWeatherData['temp'])
weatherDescription = currentWeatherData['weather'][0]['description']

def get_height_from_time_of_day(val):
    return height - ((height / 24) * val)

def get_fill_from_time_of_day(val):
    if val < sunrise_hr and val > 3:
        return twilight_color
    elif val > sunrise_hr and val < 11:
        return morning_color
    elif val > 11 and val < 3:
        return afternoon_color
    elif val > 3 and val < sunset_hr:
        return evening_color
    elif val > sunset_hr:
        return night_color

sunrise_str = get_time_from_epoch(sunrise_in_epoch, tweleve_hour_format)
sunset_str = get_time_from_epoch(sunset_in_epoch, tweleve_hour_format)

while True:
    # if not buttonA.value:
    #     print("button_pressed")
    #     format_is_tweleve_type = not format_is_tweleve_type

    # Draw a black filled box to clear the image.
    draw.rectangle((0, 0, width, height), outline=0, fill=0)
    y = top

    # #TODO: Lab 2 part D work should be filled in here. You should be able to look in cli_clock.py and stats.py
    timeValue = float(time.strftime("%H"))
    secondsValue = time.strftime("%S")

    colorHeight = get_height_from_time_of_day(timeValue)
    color = get_fill_from_time_of_day(timeValue)

    sunrise_height = get_height_from_time_of_day(sunrise_hr)
    sunset_height = get_height_from_time_of_day(sunset_hr)

    draw.rectangle((0, bottom, width, colorHeight), outline=0, fill=color)

    draw.rectangle((0, colorHeight, (int(secondsValue)/60) * width, colorHeight + 3), outline="black", fill="red")

    draw.line((0, sunrise_height, width,sunrise_height), fill=(249, 205, 28))
    draw.ellipse((0, sunrise_height-10, 20, sunrise_height+10), fill=(249, 205, 28), outline =(0,0,0))

    draw.line((0, sunset_height, width, sunset_height), fill="#FFFFFF")
    draw.ellipse((0, sunset_height-10, 20, sunset_height+10), fill = (255, 255, 255), outline =(0,0,0))

    disp.image(image, rotation)

    time.sleep(1)
