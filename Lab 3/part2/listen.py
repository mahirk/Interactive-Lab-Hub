import deepspeech
import numpy as np
import queue, os, os.path
import pyaudio
import board
import adafruit_apds9960.apds9960
import adafruit_mpr121
import busio
import random

from sys import byteorder
from array import array
import time
import gtts
from pydub import AudioSegment
from pydub.playback import play
from io import BytesIO
from pydub.utils import which, mediainfo
AudioSegment.converter = which("ffmpeg")

TASK_LIST = ['Eat two kinds of vegetable', 'No sugar drink', 'Eat fruits', 'Go for a walk', 'Learn to cook', 'Financial literacy', 'Learn something new', 'Read news', 'Get motivated', 'Organize your closet', 'Offer help', 'Volunteer work']

# Make DeepSpeech Model
model = deepspeech.Model('deepspeech-0.9.3-models.tflite')
model.enableExternalScorer('deepspeech-0.9.3-models.scorer')
i2c = busio.I2C(board.SCL, board.SDA)
mpr121 = adafruit_mpr121.MPR121(i2c)

sensor = adafruit_apds9960.apds9960.APDS9960(i2c)
sensor.enable_gesture = True
sensor.enable_proximity = True
# sensor.rotation = 270 # 270 for CLUE

THRESHOLD = 850

def is_silent(data_chunk):
    """Returns 'True' if below the 'silent' threshold"""
    snd_data = array('h', data_chunk)
    if byteorder == 'big':
        snd_data.byteswap()
    return max(snd_data) < THRESHOLD

class UserInstance(object):
    def __init__(self, name, tasks):
        self.name = name
        self.tasks = tasks

    def get_name(self):
        return self.name

    def get_task_count(self):
        return len(self.tasks)

    def get_task(self, idx):
        return self.tasks[idx] if idx < len(self.tasks) else False

    def delete_task(self, idx):
        self.tasks.pop(idx)

    def add_task(self, data):
        self.tasks.append(data)
        return len(self.tasks)

class Users(object):

    def __init__(self):
        self.user_list = ["max", "mahir", "arnavi", "alex", "arni"]
        self.user_map = {}
        for user in self.user_list:
            self.user_map[user] = UserInstance(user, random.sample(TASK_LIST, random.randint(0,len(TASK_LIST)-1)))

    def login_user(self, name):
        return self.user_map[name] if name in self.user_map else False

class AudioListener(object):

    def __init__(self):
        self.num_silent = 0
        self.snd_started = False
        self.end_recording = False
        self.buffer_queue = []

    def set_end_record(self, silent):
        if silent and self.snd_started:
            self.num_silent += 1
        elif silent and not self.snd_started:
            self.snd_started = True
        elif not silent and self.snd_started:
            self.snd_started = False
            self.num_silent = 0

        if self.snd_started and self.num_silent > 40:
            self.end_recording = True

    def get_frames(self):
        return self.buffer_queue

    def add_recording(self, data):
        self.buffer_queue.append(data)

    def get_end_record(self):
        return self.end_recording

def playsound(text):
    print(text)
    tts = gtts.gTTS(text, lang="en")
    mp3_fp = BytesIO()
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    song = AudioSegment.from_file(mp3_fp, format="mp3")
    play(song)

def get_audio_from_client():
    # Create a Streaming session
    context = model.createStream()
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    CHUNK_SIZE = 320
    capture = AudioListener()
    # Encapsulate DeepSpeech audio feeding into a callback for PyAudio
    def process_audio(in_data, frame_count, time_info, status):
        data16 = np.frombuffer(in_data, dtype=np.int16)
        capture.add_recording(data16)
        silent = is_silent(data16)
        capture.set_end_record(silent)
        return (in_data, pyaudio.paContinue)

    # PyAudio parameters
    # Feed audio to deepspeech in a callback to PyAudio
    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK_SIZE,
        stream_callback=process_audio
    )

    stream.start_stream()
    while stream.is_active() and not capture.get_end_record():
        time.sleep(0.1)

    for frame in capture.get_frames():
        context.feedAudioContent(frame)

    stream.stop_stream()
    stream.close()
    audio.terminate()
    text = context.finishStream()
    return text

def user_intro():
    playsound("Hi what is your name?")
    current_session_user = get_audio_from_client()
    user = users.login_user(current_session_user)
    while not user:
        playsound("Invalid user {}, please try again".format(current_session_user))
        current_session_user = get_audio_from_client()
        user = users.login_user(current_session_user)

    return user

def get_selection():
    touched = mpr121.touched_pins
    while True not in touched:
        touched = mpr121.touched_pins
    task_selected = touched.index(True)
    mpr121.reset()
    return task_selected

def get_task_from_selection(user: UserInstance):
    task_selected = get_selection()
    task = user.get_task(task_selected)
    if not task:
        add_task(user)
        playsound("Great! You now have {} tasks!".format(user.get_task_count()))
        return False
    else:
        playsound("You have select task number {}!".format(task_selected))
        playsound(task)
        return task_selected

def get_gesture():
    playsound("Swipe over the sensor to update the task")
    gesture = sensor.gesture()
    while gesture == 0:
        gesture = sensor.gesture()

    action = ""
    if gesture == 0x01:
        action = "up"
    elif gesture == 0x02:
        action = "down"
    elif gesture == 0x03:
        action = "left"
    elif gesture == 0x04:
        action = "right"
    playsound("Swiped {}".format(action))
    return action

def add_task(user: UserInstance):
    playsound("Adding a new task! What do you want to add?")
    task = get_audio_from_client()
    playsound("Adding {}".format(task))
    user.add_task(task)


def perform_action_from_gesture(user: UserInstance, action, task_selected):
    if action == "up" or action == "down":
        add_task(user)
    elif action == "left" or action == "right":
        user.delete_task(task_selected)
    playsound("Great! You now have {} tasks!".format(user.get_task_count()))


if __name__ == "__main__":
    users = Users()
    user = user_intro()
    playsound("Hello, {}! You have {} new tasks for today.".format(user.get_name(), user.get_task_count()))
    playsound("Please tap a button on the sensor to open your tasks")
    while True:
        task_selected = get_task_from_selection(user)
        if task_selected is not False:
            action = get_gesture()
            perform_action_from_gesture(user, action, task_selected)
        playsound("Waiting for input on the sensor.")



