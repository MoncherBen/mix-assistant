import faulthandler; faulthandler.enable()
import librosa
import numpy as np

y = np.arange(0, 648000)
y = np.float64(y)
sr = 22050

print(type(y))


env = librosa.onset.onset_strength(y=y, sr=sr)
print("env ok")

t = librosa.feature.tempo(onset_envelope=env, sr=sr)   # step 2
print("tempo ok", t)

tempo, beats = librosa.beat.beat_track(onset_envelope=env, sr=sr, bpm=120)  # step 3 (tempo estimation skipped)
print("beat_track ok")