import deepspeech
import numpy as np
import queue, os, os.path
import pyaudio
from sys import byteorder
from array import array
import time
import faulthandler
import gtts
from pydub import AudioSegment
from pydub.playback import play
import webrtcvad
from scipy import signal
from io import BytesIO
from pydub.utils import which, mediainfo
AudioSegment.converter = which("ffmpeg")

# Make DeepSpeech Model
model = deepspeech.Model('deepspeech-0.9.3-models.tflite')
model.enableExternalScorer('deepspeech-0.9.3-models.scorer')

THRESHOLD = 750

def is_silent(data_chunk):
    """Returns 'True' if below the 'silent' threshold"""
    snd_data = array('h', data_chunk)
    if byteorder == 'big':
        snd_data.byteswap()
    return max(snd_data) < THRESHOLD


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

        if self.snd_started and self.num_silent > 50:
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
    print('Final text = {}'.format(text))
    return text


while True:
    playsound("Hi what is your name?")
    detail = get_audio_from_client()
    playsound("Hello, {}! You have 5 new appointments today".format(detail))
    time.sleep(5)
    print('Restarting')
