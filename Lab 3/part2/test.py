import deepspeech
import numpy as np
import os, os.path
import pyaudio
from sys import byteorder
from array import array
import time
import faulthandler
import gtts
from pydub import AudioSegment
from pydub.playback import play
from scipy import signal



# Make DeepSpeech Model
model = deepspeech.Model('deepspeech-0.9.3-models.tflite')
model.enableExternalScorer('deepspeech-0.9.3-models.scorer')

THRESHOLD = 750


class Audio(object):
    """Streams raw audio from microphone. Data is received in a separate thread, and stored in a buffer, to be read from."""

    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    CHUNK_SIZE = 320

    def __init__(self, callback=None):
        def proxy_callback(in_data, frame_count, time_info, status):
            #pylint: disable=unused-argument
            self.buffer_queue.append(in_data)
            silent = is_silent(np.frombuffer(in_data, dtype=np.int16))
            self.set_end_record(silent)
            return (None, pyaudio.paContinue)

        self.num_silent = 0
        self.snd_started = False
        self.end_recording = False
        self.buffer_queue = []
        self.input_rate = self.RATE
        self.sample_rate = self.RATE
        self.block_size = self.CHUNK_SIZE
        self.block_size_input = self.CHUNK_SIZE
        self.pa = pyaudio.PyAudio()

        kwargs = {
            'format': self.FORMAT,
            'channels': self.CHANNELS,
            'rate': self.RATE,
            'input': True,
            'frames_per_buffer': self.block_size_input,
            'stream_callback': proxy_callback,
        }

        self.chunk = None
        self.stream = self.pa.open(**kwargs)
        self.stream.start_stream()

    def set_end_record(self, silent):
        if silent and self.snd_started:
            self.num_silent += 1
        elif silent and not self.snd_started:
            self.snd_started = True
        elif not silent and self.snd_started:
            self.snd_started = False
            self.num_silent = 0

        if self.snd_started and self.num_silent > 30:
            self.end_recording = True

    def read(self):
        """Return a block of audio data, blocking if necessary."""
        return self.buffer_queue.get()

    def destroy(self):
        self.stream.stop_stream()
        self.stream.close()
        self.pa.terminate()

def is_silent(data_chunk):
    """Returns 'True' if below the 'silent' threshold"""
    snd_data = array('h', data_chunk)
    if byteorder == 'big':
        snd_data.byteswap()
    return max(snd_data) < THRESHOLD


class AudioListener(Audio):

    def __init__(self):
        super().__init__()

    def get_frames(self):
        frames = self.read()
        for frame in frames:
            yield np.frombuffer(frame, np.int16)

    def get_end_record(self):
        return self.end_recording

def playsound(text):
    print(text)
    tts = gtts.gTTS(text, lang="en")
    mp3_fp = BytesIO()
    tts.write_to_fp(mp3_fp)
    song = AudioSegment.from_file(mp3_fp, format="mp3")
    play(song)

def get_audio_from_client():
    # Start audio with VAD
    # vad_audio = VADAudio(aggressiveness=2)
    capture = AudioListener()
    frames = capture.get_frames()
    text = ""
    stream_context = model.createStream()
    for frame in frames:
        if frame is not None:
            stream_context.feedAudioContent(frame)
        else:
            text = stream_context.finishStream()
            print("Recognized: %s" % text)
            print("get_end_record: %s" % capture.get_end_record())
            # stream_context = model.createStream()
    return text


while True:
    detail = get_audio_from_client()
    print(detail)
    time.sleep(10)
    print('Restarting')
