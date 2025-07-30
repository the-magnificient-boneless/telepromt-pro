import sys
import time
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel,
    QFileDialog, QLineEdit, QHBoxLayout, QScrollArea, QStackedLayout, QMessageBox
)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont
from mutagen import File as MutagenFile
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from mutagen.wavpack import WavPack
import pygame


def get_audio_duration(path):
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext == ".mp3":
            audio = MP3(path)
        elif ext in [".m4a", ".mp4"]:
            audio = MP4(path)
        elif ext == ".wv":
            audio = WavPack(path)
        else:
            audio = MutagenFile(path)
        if audio and audio.info:
            return audio.info.length
        else:
            return 0
    except Exception as e:
        print(f"Error al obtener duración de audio: {e}")
        return 0


def format_seconds(seconds):
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"


class ScrollAudioPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Texto con Audio y Scroll")
        self.setGeometry(100, 100, 1000, 700)

        pygame.mixer.init()

        self.font_size = 20
        self.duration = 1
        self.delay = 0
        self.countdown_value = 0
        self.scroll_paused = False
        self.current_step = 0

        self.text_file = None
        self.audio_file = None
        self.text_content = ""

        self.scroll_timer = None
        self.countdown_timer = None

        self.manual_valid = False
        self.delay_valid = False

        self.setup_ui()

    def setup_ui(self):
        self.central = QWidget()
        self.setCentralWidget(self.central)
        self.main_layout = QVBoxLayout(self.central)
        self.central.setStyleSheet("background-color: black; color: white;")

        self.top_bar = QHBoxLayout()
        self.top_bar.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.play_btn = QPushButton("▶️")
        self.play_btn.clicked.connect(self.start)

        self.pause_btn = QPushButton("⏸️")
        self.pause_btn.clicked.connect(self.toggle_pause)

        self.stop_btn = QPushButton("⏹️")
        self.stop_btn.clicked.connect(self.stop_all)

        self.increase_font_btn = QPushButton("➕")
        self.increase_font_btn.clicked.connect(lambda: self.adjust_font(2))

        self.decrease_font_btn = QPushButton("➖")
        self.decrease_font_btn.clicked.connect(lambda: self.adjust_font(-2))

        self.toggle_config_btn = QPushButton("⚙️")
        self.toggle_config_btn.clicked.connect(self.reset_config_steps)

        for btn in [self.play_btn, self.pause_btn, self.stop_btn,
                    self.increase_font_btn, self.decrease_font_btn, self.toggle_config_btn]:
            btn.setFixedWidth(50)
            self.top_bar.addWidget(btn)

        self.main_layout.addLayout(self.top_bar)

        self.countdown_bar = QLabel("")
        self.countdown_bar.setFixedHeight(80)
        self.countdown_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.countdown_bar.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        self.countdown_bar.setStyleSheet("background-color: #444; color: white;")
        self.increase_font_btn.setVisible(False)
        self.decrease_font_btn.setVisible(False)
        self.main_layout.addWidget(self.countdown_bar)

        self.stack = QStackedLayout()

        self.text_container = QWidget()
        self.text_layout = QVBoxLayout(self.text_container)
        self.text_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        self.text_layout.setContentsMargins(20, 20, 20, 100)

        self.text_label = QLabel("")
        self.text_label.setFont(QFont("Courier", self.font_size))
        self.text_label.setWordWrap(True)
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.text_label.setStyleSheet("color: rgba(255, 255, 255, 100);")
        self.text_layout.addWidget(self.text_label)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background-color: black;")
        self.scroll_area.setWidget(self.text_container)

        self.stack.addWidget(self.scroll_area)

        # Configuraciones (slides)
        self.slide1 = QWidget()
        layout1 = QVBoxLayout(self.slide1)
        layout1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.txt_btn = QPushButton("Seleccionar archivo de texto")
        self.txt_btn.clicked.connect(self.select_txt)
        layout1.addWidget(self.txt_btn)
        self.next1 = QPushButton("Siguiente")
        self.next1.clicked.connect(lambda: self.set_step(1))
        layout1.addWidget(self.next1)
        self.stack.addWidget(self.slide1)

        self.slide2 = QWidget()
        layout2 = QVBoxLayout(self.slide2)
        layout2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.audio_btn = QPushButton("Seleccionar instrumental")
        self.audio_btn.clicked.connect(self.select_audio)
        layout2.addWidget(self.audio_btn)
        self.next2 = QPushButton("Siguiente")
        self.next2.clicked.connect(lambda: self.set_step(2))
        layout2.addWidget(self.next2)
        self.stack.addWidget(self.slide2)

        self.slide3 = QWidget()
        layout3 = QVBoxLayout(self.slide3)
        layout3.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.audio_info_label = QLabel("Duración del audio: 00:00")
        layout3.addWidget(self.audio_info_label)

        delay_layout = QHBoxLayout()
        self.delay_input = QLineEdit()
        self.delay_input.setPlaceholderText("Delay (MM:SS)")
        delay_layout.addWidget(QLabel("Delay:"))
        delay_layout.addWidget(self.delay_input)
        layout3.addLayout(delay_layout)

        manual_duration_layout = QHBoxLayout()
        self.manual_duration_input = QLineEdit()
        self.manual_duration_input.setPlaceholderText("Duración (MM:SS)")
        manual_duration_layout.addWidget(QLabel("Duración manual:"))
        manual_duration_layout.addWidget(self.manual_duration_input)
        layout3.addLayout(manual_duration_layout)

        self.manual_duration_input.textChanged.connect(self.validate_manual_duration)
        self.delay_input.textChanged.connect(self.validate_delay_input)

        self.start_from_step3_btn = QPushButton("Iniciar")
        self.start_from_step3_btn.setEnabled(False)
        self.start_from_step3_btn.clicked.connect(self.start)
        layout3.addWidget(self.start_from_step3_btn)
        self.stack.addWidget(self.slide3)

        self.main_layout.addLayout(self.stack)
        self.set_step(0)

    def set_step(self, step):
        self.current_step = step
        self.stack.setCurrentIndex(step + 1 if step < 3 else 0)
        if step == 2 and self.audio_file:
            self.duration = get_audio_duration(self.audio_file) or 0
            self.audio_info_label.setText(f"Duración del audio: {format_seconds(self.duration)}")

    def validate_manual_duration(self):
        text = self.manual_duration_input.text()
        duration = self.parse_duration_input(text)
        if duration > 0:
            self.manual_duration_input.setStyleSheet("border: 2px solid green;")
            self.manual_valid = True
        else:
            self.manual_duration_input.setStyleSheet("border: 2px solid red;")
            self.manual_valid = False
        self.update_start_button_state()

    def validate_delay_input(self):
        text = self.delay_input.text()
        duration = self.parse_duration_input(text)
        if duration > 0:
            self.delay_input.setStyleSheet("border: 2px solid green;")
            self.delay_valid = True
            self.delay = duration
        else:
            self.delay_input.setStyleSheet("border: 2px solid red;")
            self.delay_valid = False
        self.update_start_button_state()

    def update_start_button_state(self):
        self.start_from_step3_btn.setEnabled(getattr(self, 'manual_valid', False) and getattr(self, 'delay_valid', False))

    def parse_duration_input(self, text):
        try:
            if ":" in text:
                parts = text.split(":")
                if len(parts) == 2:
                    mins, secs = parts
                    if mins.isdigit() and secs.isdigit():
                        return int(mins) * 60 + int(secs)
            return float(text)
        except:
            return 0

    def start(self):
        if not self.text_file or not self.audio_file:
            return

        self.delay = self.parse_duration_input(self.delay_input.text())

        manual_text = self.manual_duration_input.text()
        manual_duration = self.parse_duration_input(manual_text)
        if manual_duration <= 0:
            QMessageBox.warning(self, "Duración inválida", "Por favor ingresa una duración válida en formato minutos:segundos o en segundos.")
            return

        self.duration = manual_duration

        if self.duration <= 0:
            self.duration = 1

        self.showFullScreen()
        self.stack.setCurrentIndex(0)
        self.text_label.setStyleSheet("color: rgba(255, 255, 255, 100);")
        self.scroll_area.verticalScrollBar().setValue(0)

        pygame.mixer.music.load(self.audio_file)
        pygame.mixer.music.play()

        self.countdown_value = self.delay
        self.countdown_bar.setText(f"Comienza en {format_seconds(self.countdown_value)}...")
        self.countdown_bar.setVisible(True)

        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.update_countdown)
        self.countdown_timer.start(1000)

    def scroll_step(self):
        elapsed = time.time() - self.start_time
        if self.duration == 0:
            progress = 1.0
        else:
            progress = min(elapsed / self.duration, 1.0)

        bar = self.scroll_area.verticalScrollBar()
        bar.setValue(int(progress * bar.maximum()))

        if progress >= 1.0:
            self.scroll_timer.stop()
            self.text_label.setStyleSheet("color: rgba(255, 255, 255, 100);")

    def adjust_font(self, delta):
        bar = self.scroll_area.verticalScrollBar()

        max_scroll_before = bar.maximum()
        pos_before = bar.value()
        progress_before = pos_before / max_scroll_before if max_scroll_before > 0 else 0

        height_before = self.text_label.sizeHint().height()

        self.font_size = max(8, self.font_size + delta)
        self.text_label.setFont(QFont("Courier", self.font_size))

        self.text_label.adjustSize()
        QApplication.processEvents()

        height_after = self.text_label.sizeHint().height()
        max_scroll_after = bar.maximum()

        if height_before > 0:
            scaling_factor = height_after / height_before
            self.duration *= 1 / scaling_factor  # fuente más grande = scroll más rápido

        bar.setValue(int(progress_before * max_scroll_after))

        if self.scroll_timer and self.scroll_timer.isActive():
            new_elapsed = progress_before * self.duration
            self.start_time = time.time() - new_elapsed

    def update_countdown(self):
        self.countdown_value -= 1

        if self.countdown_value == 1:
            self.text_label.setStyleSheet("color: rgba(255, 255, 255, 255);")

        if self.countdown_value <= 0:
            self.countdown_timer.stop()
            self.countdown_bar.setVisible(False)
            self.start_time = time.time()
            self.start_scroll()
        else:
            self.countdown_bar.setText(f"Comienza en {format_seconds(self.countdown_value)}...")

    def start_scroll(self):
        self.scroll_timer = QTimer()
        self.scroll_timer.timeout.connect(self.scroll_step)
        self.scroll_timer.start(30)

    def scroll_step(self):
        elapsed = time.time() - self.start_time
        if self.duration == 0:
            progress = 1.0
        else:
            progress = min(elapsed / self.duration, 1.0)

        bar = self.scroll_area.verticalScrollBar()
        bar.setValue(int(progress * bar.maximum()))

        if progress >= 1.0:
            self.scroll_timer.stop()
            self.text_label.setStyleSheet("color: rgba(255, 255, 255, 100);")

    def adjust_font(self, delta):
        bar = self.scroll_area.verticalScrollBar()

        # Progreso actual
        max_scroll_before = bar.maximum()
        pos_before = bar.value()
        progress_before = pos_before / max_scroll_before if max_scroll_before > 0 else 0

        # Altura total antes (widget con todo el texto)
        height_before = self.text_label.sizeHint().height()

        # Cambia la fuente
        self.font_size = max(8, self.font_size + delta)
        self.text_label.setFont(QFont("Courier", self.font_size))

        # Forzar actualización del layout
        self.text_label.adjustSize()
        QApplication.processEvents()

        # Altura total después
        height_after = self.text_label.sizeHint().height()

        # Nuevo máximo scroll
        max_scroll_after = bar.maximum()

        # Ajustar duración proporcionalmente
        if height_before > 0:
            self.duration = self.duration * (height_after / height_before)

        # Ajusta valor del scroll para mantener posición proporcional
        bar.setValue(int(progress_before * max_scroll_after))

        # Ajusta start_time para mantener sincronía del scroll con el tiempo
        if self.scroll_timer and self.scroll_timer.isActive():
            new_elapsed = progress_before * self.duration
            self.start_time = time.time() - new_elapsed



    def toggle_pause(self):
        if self.scroll_paused:
            pygame.mixer.music.unpause()
            if self.scroll_timer:
                self.scroll_timer.start(30)
            self.scroll_paused = False
            self.pause_btn.setText("⏸️")
        else:
            pygame.mixer.music.pause()
            if self.scroll_timer and self.scroll_timer.isActive():
                self.scroll_timer.stop()
            self.scroll_paused = True
            self.pause_btn.setText("▶️")

    def stop_all(self):
        pygame.mixer.music.stop()
        if self.scroll_timer:
            self.scroll_timer.stop()
        if self.countdown_timer:
            self.countdown_timer.stop()

        self.scroll_area.verticalScrollBar().setValue(0)
        self.text_label.setStyleSheet("color: rgba(255, 255, 255, 100);")
        self.countdown_bar.setVisible(False)
        self.showNormal()
        self.scroll_paused = False
        self.pause_btn.setText("⏸️")
        self.set_step(0)


    def reset_config_steps(self):
        # Resetea a paso 1
        self.stop_all()
        self.set_step(0)

    def select_txt(self):
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo de texto", "", "Text Files (*.txt);;All Files (*)")
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.text_content = f.read()
                self.text_label.setText(self.text_content)
                self.text_file = path
                self.next1.setEnabled(True)
                self.increase_font_btn.setVisible(True)
                self.decrease_font_btn.setVisible(True)

            except Exception as e:
                QMessageBox.warning(self, "Error", f"No se pudo leer el archivo: {e}")

    def select_audio(self):
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo de audio", "", "Audio Files (*.mp3 *.wav *.m4a *.mp4 *.wv);;All Files (*)")
        if path:
            self.audio_file = path
            self.next2.setEnabled(True)
            if self.current_step == 2:
                self.duration = get_audio_duration(self.audio_file) or 0
                self.audio_info_label.setText(f"Duración del audio: {format_seconds(self.duration)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ScrollAudioPlayer()
    window.show()
    sys.exit(app.exec())
