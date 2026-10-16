"""
####### audio_engine.py #######

### Auth: MoncherBen, Oct. 2026
"""


import threading

import numpy as np
import sounddevice as sd


SAMPLE_RATE = 44100
CHANNELS = 2



class AudioEngine:
    """ The process that manages the sounds streaming. """

    def __init__(self):
        """ Typically. """
        self._lock = threading.Lock()
        self._tracks = {"A": {"audio": None,
                              "position": 0,
                              "playing": False,
                              "gain": 1.0},
                        "B": {"audio": None,
                              "position": 0,
                              "playing": False,
                              "gain": 1.0}}

        self.stream = sd.OutputStream(samplerate=SAMPLE_RATE,
                                      channels=CHANNELS,
                                      dtype="float32",
                                      callback=self._audio_callback,
                                      blocksize=1024)
        self.stream.start()

    @staticmethod
    def _to_stereo(audio: np.ndarray) -> np.ndarray:
        """ Convert any audio to stereo.
        
            audio (np.ndarray): the audio content

            (np.ndarray) -> the stereo audio content
        """
        # Éntrée attendue : (canaux, échantillons)
        if audio.ndim == 1:
            audio = audio[np.newaxis, :]

        if audio.shape[0] == 1:
            audio = np.repeat(audio, 2, axis=0)
        elif audio.shape[0] > 2:
            audio = audio[:2, :]

        # Format de sortie : (échantillons, canaux)
        return np.ascontiguousarray(audio.T, dtype=np.float32)

    def load_audio(self, deck_id: str, audio: np.ndarray):
        """ Typically.
        
            deck_id (str): the id of the loaded track
            audio (np.ndarray): the audio content
        """
        stereo = self._to_stereo(audio)

        with self._lock:
            track = self._tracks[deck_id]
            track["playing"] = False
            track["audio"] = stereo
            track["position"] = 0

    def play(self, deck_id: str):
        """ Typically.
        
            deck_id (str): the id of the loaded track
        """
        with self._lock:
            track = self._tracks[deck_id]
            if track["audio"] is not None:
                if track["position"] >= len(track["audio"]):
                    track["position"] = 0
                track["playing"] = True

    def pause(self, deck_id: str):
        """ Typically.
        
            deck_id (str): the id of the loaded track
        """
        with self._lock:
            self._tracks[deck_id]["playing"] = False

    def stop(self, deck_id: str):
        """ Typically.
        
            deck_id (str): the id of the loaded track
        """
        with self._lock:
            track = self._tracks[deck_id]
            track["playing"] = False
            track["position"] = 0
    
    def set_gain(self, deck_id: str, gain: float):
        """ Typically.
        
            deck_id (str): the id of the loaded track
        """
        with self._lock:
            self._tracks[deck_id]["gain"] = float(np.clip(gain, 0.0, 1.0))

    def _audio_callback(self, outdata, frames, time_info, status):
        """ Plays the audio. """
        # Silence par défaut, même en cas de fin de morceau.
        outdata.fill(0)

        with self._lock:
            for track in self._tracks.values():
                audio = track["audio"]

                if audio is None or not track["playing"]:
                    continue

                start = track["position"]
                end = min(start + frames, len(audio))

                if start >= end:
                    track["playing"] = False
                    continue

                count = end - start
                outdata[:count] += audio[start:end] * track["gain"]
                track["position"] = end

                if end >= len(audio):
                    track["playing"] = False

        # Évite l'écrêtage lorsque les deux pistes jouent ensemble.
        np.clip(outdata, -1.0, 1.0, out=outdata)

    def close(self):
        """ Typically. """
        if self.stream.active:
            self.stream.stop()
        self.stream.close()