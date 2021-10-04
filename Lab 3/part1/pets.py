from vosk import Model, KaldiRecognizer
import sys
import os
import wave
import json
import gtts
import os
import sys

def playsound(text):
    print(text)
    tts = gtts.gTTS(text, lang="en")
    tts.save("speak.mp3")
    os.system("mplayer -ao alsa -really-quiet -noconsolecontrols speak.mp3")

def get_multiplier(length):
    def multiplier(idx):
        multiplier_val = (10 * (length - idx))
        return multiplier_val if multiplier_val > 0 else 1
    return multiplier

digit_map = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9
}

if not os.path.exists("model"):
    print ("Please download the model from https://github.com/alphacep/vosk-api/blob/master/doc/models.md and unpack as 'model' in the current folder.")
    exit (1)

wf = wave.open(sys.argv[1], "rb")
if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
    print ("Audio file must be WAV format mono PCM.")
    exit (1)

model = Model("model")
# Large vocabulary free form recognition
rec = KaldiRecognizer(model, wf.getframerate(), '["oh one two three four five six seven eight nine zero", "[unk]"]')
final_text = ""

while True:
    data = wf.readframes(4000)
    if len(data) == 0:
        break
    if rec.AcceptWaveform(data):
        res = json.loads(rec.Result())
        # print(res)
        # print(res['text'])
        final_text += res['text']

digits = final_text.split()
count = 0
fnc = get_multiplier(len(digits) - 1)
for idx in range(len(digits)):
    if digits[idx] in digit_map:
        count += (digit_map[digits[idx]] * fnc(idx))
    else:
        playsound("Incorrect word: {}".format(digits[idx]))

playsound("You have {} pets! That is amazing!".format(count))