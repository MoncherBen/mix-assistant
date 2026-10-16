"""
####### main_window.py #######

### Auth: MoncherBen, Oct. 2026
"""


from pathlib import Path

import librosa

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QGroupBox,
    QDoubleSpinBox
)

from src.audio.analyzer import analyze_bpm
from src.audio.audio_engine import AudioEngine, SAMPLE_RATE
from src.audio.mix_controller import (
    calculate_average_bpm,
    calculate_tempo_change,
    is_within_recommended_range,
)



class BPMWorker(QThread):
    """ The process that analyse the bpm for a given audio file. """
    bpm_ready = Signal(str, float)
    failed = Signal(str, str)

    def __init__(self, deck_id:str, file_path: str):
        """ Typically.
        
            deck_id (str):  the id of the loaded track
            file_path (str): the path of the track to load
        """
        super().__init__()
        self.deck_id = deck_id
        self.file_path = file_path

    def run(self):
        """ Typically. """
        try:
            bpm = analyze_bpm(self.file_path)
            self.bpm_ready.emit(self.deck_id, bpm)
        except Exception as exc:
            self.failed.emit(self.deck_id, str(exc))



class AudioLoadWorker(QThread):
    audio_ready = Signal(str, object)
    failed = Signal(str, str)

    def __init__(self, deck_id: str, file_path: str):
        super().__init__()
        self.deck_id = deck_id
        self.file_path = file_path

    def run(self):
        try:
            audio, _ = librosa.load(
                self.file_path,
                sr=SAMPLE_RATE,
                mono=False,
            )
            self.audio_ready.emit(self.deck_id, audio)
        except Exception as exc:
            self.failed.emit(self.deck_id, str(exc))



class MainWindow(QMainWindow):
    """ Typically. """

    def __init__(self):
        """ Typically. """
        super().__init__()

        self.setWindowTitle("MoncherBen's Mix Assistant")
        self.resize(900, 500)

        self.track_paths = {"A": None, "B": None}
        self.track_labels = {}
        self.bpm_inputs = {}
        self.load_buttons = {}
        self.analysis_workers = {}
        self.tempo_labels = {}
        self.audio_engine = AudioEngine()
        self.audio_workers = {}
        self.play_buttons = {}

        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)

        title = QLabel("MoncherBen's Mix Assistant")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")

        decks_layout = QHBoxLayout()

        for deck_id in ("A", "B"):
            group = QGroupBox(f"Deck {deck_id}")
            layout = QVBoxLayout(group)

            track_label = QLabel("Aucun morceau chargé")
            track_label.setWordWrap(True)

            bpm_label = QLabel("BPM (détecté ou corrigé) :")

            bpm_input = QDoubleSpinBox()
            bpm_input.stepType()
            bpm_input.setRange(40, 240)
            bpm_input.setValue(int(120))
            bpm_input.setSuffix(" BPM")
            bpm_input.valueChanged.connect(self.update_tempo_info)

            load_button = QPushButton("Charger un morceau")
            load_button.clicked.connect(lambda checked=False, d=deck_id: self.load_track(d))

            tempo_label = QLabel("Variation : —")
            self.tempo_labels[deck_id] = tempo_label

            layout.addWidget(track_label)
            layout.addWidget(bpm_label)
            layout.addWidget(bpm_input)
            layout.addWidget(tempo_label)
            layout.addStretch()
            layout.addWidget(load_button)

            self.track_labels[deck_id] = track_label
            self.bpm_inputs[deck_id] = bpm_input
            self.load_buttons[deck_id] = load_button

            decks_layout.addWidget(group)

            play_button = QPushButton("Lecture")
            pause_button = QPushButton("Pause")
            stop_button = QPushButton("Arrêt")

            play_button.clicked.connect(
                lambda checked=False, d=deck_id: self.audio_engine.play(d)
            )
            pause_button.clicked.connect(
                lambda checked=False, d=deck_id: self.audio_engine.pause(d)
            )
            stop_button.clicked.connect(
                lambda checked=False, d=deck_id: self.audio_engine.stop(d)
            )

            layout.addWidget(play_button)
            layout.addWidget(pause_button)
            layout.addWidget(stop_button)

            self.play_buttons[deck_id] = play_button

        self.status_label = QLabel("Chargez deux morceaux pour commencer.")

        target_group = QGroupBox("Tempo cible")
        target_layout = QVBoxLayout(target_group)

        self.target_bpm = QDoubleSpinBox()
        self.target_bpm.setRange(40.0, 240.0)
        self.target_bpm.setDecimals(1)
        self.target_bpm.setSingleStep(0.5)
        self.target_bpm.setValue(120.0)
        self.target_bpm.setSuffix(" BPM")
        self.target_bpm.valueChanged.connect(self.update_tempo_info)

        buttons_layout = QHBoxLayout()

        use_a_button = QPushButton("Prendre le BPM de A")
        use_a_button.clicked.connect(
            lambda: self.target_bpm.setValue(
                self.bpm_inputs["A"].value()
            )
        )

        use_b_button = QPushButton("Prendre le BPM de B")
        use_b_button.clicked.connect(
            lambda: self.target_bpm.setValue(
                self.bpm_inputs["B"].value()
            )
        )

        average_button = QPushButton("BPM moyen")
        average_button.clicked.connect(self.use_average_bpm)

        buttons_layout.addWidget(use_a_button)
        buttons_layout.addWidget(use_b_button)
        buttons_layout.addWidget(average_button)

        target_layout.addWidget(QLabel("Choisir le tempo commun :"))
        target_layout.addWidget(self.target_bpm)
        target_layout.addLayout(buttons_layout)

        main_layout.addWidget(title)
        main_layout.addLayout(decks_layout)
        main_layout.addWidget(target_group)


        main_layout.addWidget(self.status_label)

        self.setCentralWidget(central_widget)

        self.update_tempo_info()

    def load_track(self, deck_id: str):
        """ Load a track with a file dialog interface.
        
            deck_id (str):  the id of the loaded track
        """
        # Avoids the track being replaced during its analyze
        current_worker = self.analysis_workers.get(deck_id)
        if current_worker is not None and current_worker.isRunning():
            self.status_label.setText(f"Analyse du deck {deck_id} déjà en cours.")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Charger le morceau {deck_id}",
            "",
            "Fichiers audio (*.wav *.mp3);;"
            "Tous les fichiers (*)"
        )

        if not file_path:
            return

        self.track_paths[deck_id] = Path(file_path)
        self.track_labels[deck_id].setText(self.track_paths[deck_id].name)
        self.load_buttons[deck_id].setEnabled(False)

        self.status_label.setText(f"Analyse du BPM du deck {deck_id} en cours...")

        worker = BPMWorker(deck_id, file_path)
        self.analysis_workers[deck_id] = worker

        worker.bpm_ready.connect(self.on_bpm_ready)
        worker.failed.connect(self.on_analysis_failed)
        worker.finished.connect(lambda d=deck_id, w=worker: self.on_worker_finished(d, w))

        worker.start()

        audio_worker = AudioLoadWorker(deck_id, file_path)
        self.audio_workers[deck_id] = audio_worker

        audio_worker.audio_ready.connect(self.on_audio_ready)
        audio_worker.failed.connect(self.on_audio_failed)
        audio_worker.finished.connect(lambda d=deck_id,
                                      w=audio_worker: self.on_audio_worker_finished(d, w))
        audio_worker.start()

    def on_bpm_ready(self, deck_id: str, bpm: float):
        """ Treats a found bpm.
        
            deck_id (str):  the id of the loaded track
            bpm (float): bpm value
        """
        bpm = round(bpm)
        self.bpm_inputs[deck_id].setValue(bpm)
        self.status_label.setText(
            f"Deck {deck_id} : BPM estimé à {bpm}. Tu peux corriger cette valeur manuellement."
        )

    def on_analysis_failed(self, deck_id: str, message: str):
        """ Typically.
        
            deck_id (str):  the id of the loaded track
            message (str): the error message
        """
        self.status_label.setText(f"Échec de l'analyse du deck {deck_id} : {message}")

    def on_worker_finished(self, deck_id: str, worker: BPMWorker):
        """ Typically.

            deck_id (str): the id of the loaded track
            worker (BPMWorker) : the QThread that analyse the bpm for a given audio file.
        """
        self.load_buttons[deck_id].setEnabled(True)

        if self.analysis_workers.get(deck_id) is worker:
            del self.analysis_workers[deck_id]

        worker.deleteLater()

    def use_average_bpm(self):
        bpm_a = self.bpm_inputs["A"].value()
        bpm_b = self.bpm_inputs["B"].value()

        target = calculate_average_bpm(bpm_a, bpm_b)
        self.target_bpm.setValue(target)

    def update_tempo_info(self, *_):
        target = self.target_bpm.value()

        for deck_id in ("A", "B"):
            source = self.bpm_inputs[deck_id].value()

            change = calculate_tempo_change(source, target)
            within_range = is_within_recommended_range(
                source, target
            )

            status = "OK" if within_range else "Variation élevée"

            self.tempo_labels[deck_id].setText(
                f"Variation : {change:+.2f} % — {status}"
            )

    def closeEvent(self, event):
        workers = (list(self.analysis_workers.values()) + list(self.audio_workers.values()))

        for worker in workers:
            if worker.isRunning():
                worker.wait()

        self.audio_engine.close()
        event.accept()
    
    def on_audio_ready(self, deck_id: str, audio):
        self.audio_engine.load_audio(deck_id, audio)
        self.status_label.setText(
            f"Deck {deck_id} prêt : lecture disponible."
        )

    def on_audio_failed(self, deck_id: str, message: str):
        self.status_label.setText(
            f"Erreur de chargement audio sur {deck_id} : {message}"
        )

    
    def on_audio_worker_finished(self, deck_id: str, worker):
        if self.audio_workers.get(deck_id) is worker:
            del self.audio_workers[deck_id]
        worker.deleteLater()

