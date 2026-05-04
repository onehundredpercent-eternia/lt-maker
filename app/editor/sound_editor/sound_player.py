from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QMessageBox
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QLabel, QProgressBar
import pygame
import os
import time


class SoundPlayer:
    def __init__(self, view, parent_layout):
        self.view = view
        self.layout = parent_layout

        pygame.mixer.init()

        # Audio states
        self.current_track = None
        self.current_track_name : str | None = None
        self.duration = 0
        self.start_time = 0
        self.pause_time = 0
        self.is_playing = False
        self.is_paused = False

        # Audio player UI
        self.audio_player_widget = QWidget()
        player_layout = QVBoxLayout(self.audio_player_widget)

        self.file_label = QLabel("No track selected")
        player_layout.addWidget(self.file_label)

        # Init time and progress widget
        progress_row = QHBoxLayout()
        self.current_time_label = QLabel("--:--")
        self.duration_label = QLabel("--:--")
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(6)
        progress_row.addWidget(self.current_time_label)
        progress_row.addWidget(self.progress, 1)  # stretch = 1 (fills space)
        progress_row.addWidget(self.duration_label)
        player_layout.addLayout(progress_row)

        # Init control buttons
        controls = QHBoxLayout()
        self.play_pause_button = QPushButton("Play")
        self.stop_button = QPushButton("Stop")

        controls.addWidget(self.play_pause_button)
        controls.addWidget(self.stop_button)
        player_layout.addLayout(controls)

        self.layout.addWidget(self.audio_player_widget)
        self.audio_player_widget.setEnabled(False)

        # Connect control button signals
        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        self.stop_button.clicked.connect(self.stop_audio)

        # Timer for progress
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_position)
        self.timer.start(100)

    def load_track(self, file_path: str):
        try:
            self.current_track = pygame.mixer.Sound(file_path)
            self.duration = int(self.current_track.get_length() * 1000)
        except pygame.error as e:
            QMessageBox.critical(
                self,
                "Audio Error",
                f"Failed to load audio file:\n{file_path}\n\n{e}"
            )
            self.current_track = None

    def handle_audio_player_on_select(self, has_selection: bool, selected_track):
        self.audio_player_widget.setEnabled(has_selection)

        if not has_selection or not selected_track:
            self.stop_current_track()
            self.clear_track_states()
            self.reset_audio_states()
            self.clear_audio_ui_states()
            return

        file_path = selected_track.full_path
        selected_track_name = getattr(selected_track, "nid", "Unknown")

        if self.current_track_name and self.current_track_name != selected_track_name:
            self.stop_current_track()
            self.clear_track_states()
            self.reset_audio_states()
            self.clear_audio_ui_states()

        if not os.path.exists(file_path):
            self.file_label.setText("❌ File not found")
            return
        
        self.current_track_name = selected_track_name
        self.file_label.setText(f"Track name: {self.current_track_name}\nFile path: {file_path}")
        self.load_track(file_path)
        self.update_time_label(0, self.duration)

    def toggle_play_pause(self):
        if not self.current_track:
            return

        if not self.is_paused and self.play_pause_button.text() == "Pause":
            pygame.mixer.pause()
            self.is_paused = True
            self.pause_time = self.get_time_now_ms()
            self.play_pause_button.setText("Play")
        else:
            if self.is_paused:
                pygame.mixer.unpause()
                paused_duration = self.get_time_now_ms() - self.pause_time
                self.start_time += paused_duration
                self.is_paused = False
            else:
                self.current_track.play()
                self.start_time = self.get_time_now_ms()
                self.is_playing = True

            self.play_pause_button.setText("Pause")

    def reset_audio_states(self):
        self.is_playing = False
        self.is_paused = False
        self.start_time = 0
        self.pause_time = 0

    def clear_track_states(self):
        self.current_track = None
        self.current_track_name = None

    def clear_audio_ui_states(self):
        """
        Clear audio ui states back to non-selection
        """

        self.file_label.setText("No track selected")
        self.play_pause_button.setText("Play")
        self.progress.setValue(0)
        self.current_time_label.setText("--:--")
        self.duration_label.setText("--:--")

    def reset_audio_ui_states(self):
        """
        Reset audio ui state while on selection
        """

        self.play_pause_button.setText("Play")
        self.progress.setValue(0)
        self.update_time_label(0, self.duration)

    def stop_current_track(self):
        if self.current_track:
            self.current_track.stop()

    def stop_audio(self):
        self.stop_current_track()
        self.reset_audio_states()
        self.reset_audio_ui_states()

    def stop_audio_on_close_event(self):
        """
        Stop audio when the parent UI closes.
        Add this function to Qwidget.closeEvent
        """

        self.stop_current_track()

    def update_position(self):
        """
        Track audio player progress and update audio states
        """

        # Check if track exists
        if not self.is_playing or not self.current_track:
            return

        now = self.get_time_now_ms()

        # Compute current play time
        if self.is_paused:
            current = self.pause_time - self.start_time
        else:
            current = now - self.start_time

        if self.duration > 0:
            current = max(0, min(current, self.duration))
            percent = int((current / self.duration) * 100)

            # Update progress widget
            self.progress.setValue(percent)
            self.progress.update()
        else:
            QMessageBox.critical(
                self,
                "Audio Error",
                "Duration is 0 (audio not loaded correctly)"
            )

        self.update_time_label(int(current), self.duration)

        # Check if the track finishes
        if self.duration > 0 and current >= self.duration:
            self.reset_audio_states()
            self.reset_audio_ui_states()

    def get_time_now_ms(self) -> int:
        current = time.monotonic() * 1000
        return int(current)

    def fmt_time(self, milisec : int) -> str:
        s = milisec // 1000
        return f"{s//60:02}:{s%60:02}"

    def update_time_label(self, position: int, duration: int):
        self.current_time_label.setText(self.fmt_time(position))
        self.duration_label.setText(self.fmt_time(duration))
