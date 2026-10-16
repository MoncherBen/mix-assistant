"""
####### analyzer.py #######

### Auth: MoncherBen, Oct. 2026
"""


import librosa
import numpy as np



def analyze_bpm(file_path) -> float:
    """
    Estimate the rhythm and return the bpm.

    file_path (path): path to the audio
    
    -> (float): the estimated bpm
    """
    y, sr = librosa.load(file_path, sr=22050, mono=True)

    env = librosa.onset.onset_strength(y=y, sr=sr)

    if y.size == 0:
        raise ValueError("Le fichier audio est vide.")

    tempo = librosa.feature.tempo(onset_envelope=env, sr=sr)

    bpm = float(np.asarray(tempo).reshape(-1)[0])

    if not np.isfinite(bpm) or bpm <= 0:
        raise ValueError("Impossible de détecter un BPM valide.")

    return bpm