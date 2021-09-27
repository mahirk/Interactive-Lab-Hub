import time
import subprocess
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789
import adafruit_apds9960.apds9960
import geocoder
import requests
import datetime
import busio

i2c = busio.I2C(board.SCL, board.SDA)
sensor = adafruit_apds9960.apds9960.APDS9960(i2c)
sensor.enable_proximity = True

VIEW_MODE_FILL =  'VIEW_MODE_FILL'
VIEW_MODE_TIDE =  'VIEW_MODE_TIDE'
view_mode = VIEW_MODE_TIDE

tweleve_hour_format = "%I:%M %p"

imageMap = {}

twilight_color = (75,0,130)
morning_color = (255, 249, 121)
afternoon_color = (229, 222, 68)
evening_color = (239, 129, 14)
night_color = (5, 55, 82)

water_color = (27,163,236)
water_color_deep = (0, 50, 156)
high_tide_height = - 35
low_tide_height = - 15

images_url = "https://openweathermap.org/img/wn/{}@2x.png"
tide_api = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?begin_date={}&end_date={}&station=8518750&product=predictions&datum=STND&time_zone=gmt&interval=hilo&units=english&format=json"

def get_time_from_epoch(val, fmt = "%H"):
    timestamp = datetime.datetime.fromtimestamp(val)
    return timestamp.strftime(fmt)

def normalize_tide_data(tide_data):
    predictions = tide_data['predictions']
    return_val = []
    for prediction in predictions:
        time_for_tide = datetime.datetime.fromisoformat(prediction["t"])
        return_val.append((time_for_tide, prediction["type"]))
    return return_val

def load_tide_data():
    headers = {
        'cache-control': "no-cache",
    }

    # dd/mm/YY
    d1 = time.strftime("%Y%m%d")

    response = requests.request("GET", tide_api.format(d1, d1), headers=headers)
    return response.json()

def load_weather_data():
    g = geocoder.ip('me')
    latitude = str(g.latlng[0])
    longitude = str(g.latlng[1])

    weather_url = "https://api.openweathermap.org/data/2.5/onecall"

    querystring = {
        "lat":latitude,
        "lon":longitude,
        "exclude":"hourly,minutely",
        "appid":"33a1154b742cf3f8f1a8e4ecd4341183"
    }

    headers = {
        'cache-control': "no-cache",
    }

    response = requests.request("GET", weather_url, headers=headers, params=querystring)
    return response.json()

def convert_kelvin_to_farenheight(kelvin):
    d_f = (kelvin - 273.15) * 9/5 + 32
    return "{:.1f} °F".format(d_f)

def get_image_item_for_display(key):
    imagepng = "{}.png".format(key)
    if imagepng not in imageMap:
        rawPngImage = requests.get(images_url.format(key), stream=True).raw
        png = Image.open(rawPngImage)
        png.load() # required for png.split()
        background = Image.new("RGB", png.size, (0,0,0))
        background.paste(png, mask=png.split()[3]) # 3 is the alpha channel
        imageMap[imagepng] = background.rotate(90)
    return imageMap[imagepng]


weatherData = load_weather_data()
tide_data = normalize_tide_data(load_tide_data())

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

def get_fill_from_time_of_day(val, get_darker=False):
    if val < sunrise_hr and val > 3:
        return twilight_color
    elif val > sunrise_hr and val <= 11:
        return morning_color
    elif val > 11 and val <= 3:
        return afternoon_color
    elif val > 3 and val <= sunset_hr:
        return evening_color
    elif val > sunset_hr:
        return night_color if not get_darker else (0, 0, 0)

def get_water_from_time_of_day(tide_type):
    if tide_type == "H":
        return water_color_deep, height + high_tide_height
    else:
        return water_color, height + low_tide_height

def get_tide_from_time_of_day(val):
    cur_tide_type = "L"
    for tide_time, tide_type in tide_data:
        if val > float(tide_time.strftime("%H")):
            cur_tide_type = tide_type
    return cur_tide_type


sunrise_str = get_time_from_epoch(sunrise_in_epoch, tweleve_hour_format)
sunset_str = get_time_from_epoch(sunset_in_epoch, tweleve_hour_format)

def filler_time():
    timeValue = float(time.strftime("%H"))
    secondsValue = time.strftime("%S")

    colorHeight = get_height_from_time_of_day(timeValue)
    color = get_fill_from_time_of_day(timeValue)

    sunrise_height = get_height_from_time_of_day(sunrise_hr)
    sunset_height = get_height_from_time_of_day(sunset_hr)

    draw.rectangle((0, bottom, width, colorHeight), outline=0, fill=color)

    draw.rectangle((0, colorHeight, (int(secondsValue) / 60) * width, colorHeight + 3), outline="black", fill="red")

    ## SUN
    draw.line((0, sunrise_height, width, sunrise_height), fill=(249, 205, 28))
    draw.ellipse((width - 20, sunrise_height - 10, width, sunrise_height + 10), fill=(249, 205, 28), outline=(0, 0, 0))

    ## MOON
    draw.line((0, sunset_height, width, sunset_height), fill="#FFFFFF")
    draw.ellipse((0, sunset_height - 10, 20, sunset_height + 10), fill=(255, 255, 255), outline=(0, 0, 0))

def display_weather():
    disp.image(image, rotation)
    weather_image = get_image_item_for_display(currentWeatherData['weather'][0]['icon'])
    weather_image_draw = ImageDraw.Draw(weather_image)
    weather_image_draw.text((25, 0), currentTemp, font=fontWeather, fill="#FFFFFF")
    image_x, image_y = weather_image.size
    x_i = int((width / 2) + image_x / 2)
    y_i = int((height / 2) - image_y)
    disp.image(
        weather_image,
        rotation,
        15, 70
    )

def draw_celestial(time_of_day):
    if time_of_day < sunrise_hr and time_of_day > 3:
        draw.ellipse((width - 30, 50, width - 10, 70), fill=(239,155,27), outline=(0, 0, 0))
    elif time_of_day > sunrise_hr and time_of_day <= 11:
        draw.ellipse((width - 30, 10, width - 10, 30), fill=(242,221,42), outline=(0, 0, 0))
    elif time_of_day > 11 and time_of_day <= 15:
        draw.ellipse((width - 120, 10, width - 100, 30), fill=(242,226,111), outline=(0, 0, 0))
    elif time_of_day > 15 and time_of_day <= sunset_hr:
        draw.ellipse((65, 10, 85, 30), fill=(227,147,25), outline=(0, 0, 0))
    elif time_of_day > sunset_hr:
        draw.ellipse((10, 10, 30, 30), fill=(255, 255, 255), outline=(0, 0, 0))


def tide_time():
    center_width = width / 2
    timeValue = 23
    ## Color background according to time of day
    color = get_fill_from_time_of_day(timeValue, True)
    draw.rectangle((0, 0, width, height), outline=0, fill=color)

    ## Color ocean based on time of day
    cur_tide = get_tide_from_time_of_day(timeValue)
    tide_color, tide_height = get_water_from_time_of_day(cur_tide)
    draw.rectangle((0, bottom, width, tide_height), outline=0, fill=tide_color)

    ## Draw Tide texture
    draw.polygon([
        (0, tide_height),
        (20, tide_height - 5),
        (40, tide_height - 2),
        (80, tide_height + 5),
        (100, tide_height + 2),
        (120, tide_height - 5),
        (140, tide_height),
        (160, tide_height + 5),
        (180, tide_height + 2),
        (200, tide_height - 2),
        (width, tide_height),
    ], fill=tide_color)


    ## Draw haystack rock
    draw.polygon([
        (center_width - 20, height),
        (center_width - 10, height - 10),
        (center_width, height - 30),
        (center_width + 15, height - 55),
        (center_width + 20, height - 60),
        (center_width + 40, height - 75),
        (center_width + 45, height - 65),
        (center_width + 50, height - 57),
        (center_width + 70, height - 45),
        (center_width + 90, height - 35),
        (center_width + 100, height - 15),
        (center_width + 110, height),
    ], fill=(139, 69, 19))
    draw_celestial(timeValue)


while True:
    # #TODO: Lab 2 part D work should be filled in here. You should be able to look in cli_clock.py and stats.py

    if not buttonA.value:
        print("button_pressed - A")
        view_mode = VIEW_MODE_FILL
    elif not buttonB.value:
        print("button_pressed -  B")
        view_mode = VIEW_MODE_TIDE

    # Draw a black filled box to clear the image.
    draw.rectangle((0, 0, width, height), outline=0, fill=0)
    y = top
    prox = sensor.proximity
    if prox > 0:
        display_weather()
    else:
        if view_mode == VIEW_MODE_FILL:
            filler_time()
        elif view_mode == VIEW_MODE_TIDE:
            tide_time()

        disp.image(image, rotation)

    time.sleep(0.5)
