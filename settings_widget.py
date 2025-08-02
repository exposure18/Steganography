# ui/settings_widget.py — Preferences and global settings (Revised for QStackedWidget integration)

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QCheckBox, QGroupBox, QHBoxLayout,
    QPushButton, QDialogButtonBox
)
from PyQt5.QtCore import Qt, pyqtSignal # Import pyqtSignal for custom signals

class SettingsWidget(QWidget): # It remains QWidget as it's part of a QStackedWidget
    # Define a signal to be emitted when the user finishes with settings (OK/Cancel clicked).
    # This tells the parent (MainWindow) to switch views back to the main menu.
    settings_closed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Audio Settings Group Box
        audio_group = QGroupBox("Audio Feedback")
        audio_layout = QHBoxLayout()
        self.audio_enabled = QCheckBox("Enable audio cues")
        self.audio_enabled.setChecked(True) # Default to enabled
        audio_layout.addWidget(self.audio_enabled)
        audio_group.setLayout(audio_layout)
        layout.addWidget(audio_group)

        # Theme Settings Group Box
        theme_group = QGroupBox("Appearance")
        theme_layout = QHBoxLayout()
        self.dark_mode = QCheckBox("Enable dark theme")
        self.dark_mode.setChecked(True) # Default to dark theme
        theme_layout.addWidget(self.dark_mode)
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)

        # Add a stretchable space to push the buttons to the bottom
        layout.addStretch(1)

        # --- Add OK and Cancel Buttons using QDialogButtonBox ---
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        # Connect the accepted (OK) signal to our custom accept_settings method
        self.button_box.accepted.connect(self.accept_settings)
        # Connect the rejected (Cancel) signal to our custom reject_settings method
        self.button_box.rejected.connect(self.reject_settings)

        # Add the button box to the main layout
        layout.addWidget(self.button_box)
        # --- End Button Addition ---

        self.setLayout(layout)

    def get_settings(self):
        """
        Retrieves the current state of the settings from the UI elements.
        """
        return {
            "audio_enabled": self.audio_enabled.isChecked(),
            "dark_mode": self.dark_mode.isChecked()
        }

    def accept_settings(self):
        """
        Method called when the 'OK' button is clicked.
        Here you would typically save the settings (e.g., to a configuration file
        or apply them immediately to the main application).
        Then, signal the parent to switch back to the main menu.
        """
        print("Settings Accepted:", self.get_settings())
        # In a real application, you'd save these settings persistently here.
        self.settings_closed.emit() # Signal to parent that settings interaction is done

    def reject_settings(self):
        """
        Method called when the 'Cancel' button is clicked.
        Discards any changes made in the dialog and signals the parent to switch back.
        """
        print("Settings Rejected. Changes not applied.")
        self.settings_closed.emit() # Signal to parent that settings interaction is done