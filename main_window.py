# ui/main_window.py — Central GUI container for Rygelock (Refined header and hover underline effects with image-based speaker icons)

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QStackedWidget, QSpacerItem, QSizePolicy
)
from PyQt5.QtGui import QIcon, QFont, QPixmap
from PyQt5.QtCore import Qt, QSize

from ui.embed_widget import EmbedWidget
from ui.extract_widget import ExtractWidget
from ui.settings_widget import SettingsWidget # Ensure this is correctly imported

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rygelock Steganography")
        self.setGeometry(100, 100, 1100, 750)
        self.setWindowIcon(QIcon("assets/logo.png"))
        self.setStyleSheet("background-color: #121212; color: white;")

        self.central_stack = QStackedWidget()
        self.setCentralWidget(self.central_stack)

        self.is_muted = False  # Track mute state
        self.init_main_menu()
        self.init_embed_menu()
        self.init_extract_menu()
        self.init_settings_menu() # Call init_settings_menu last, so settings_widget is initialized

    def init_main_menu(self):
        main_menu = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header = QHBoxLayout()
        header.setContentsMargins(20, 20, 20, 10)

        logo_button = QPushButton()
        logo_button.setIcon(QIcon("assets/logo.png"))
        logo_button.setIconSize(QSize(96, 96))
        logo_button.setFixedSize(104, 104)
        logo_button.setStyleSheet("background-color: transparent; border: none;")
        logo_button.clicked.connect(lambda: self.central_stack.setCurrentIndex(0))

        nav_button_style = """
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                font-size: 18px;
            }
            QPushButton:hover {
                border-bottom: 2px solid #ffaa00;
            }
        """

        settings_btn = QPushButton("Settings")
        settings_btn.setStyleSheet(nav_button_style)
        # This connects to show the settings page in the stacked widget
        settings_btn.clicked.connect(lambda: self.central_stack.setCurrentIndex(3))

        logs_btn = QPushButton("Logs")
        logs_btn.setStyleSheet(nav_button_style)
        # logs_btn.clicked.connect(self.show_logs) # You would connect this to a log view

        self.mute_button = QPushButton()
        self.mute_button.setIcon(QIcon("assets/audio.png"))
        self.mute_button.setIconSize(QSize(48, 48))
        self.mute_button.setFixedSize(64, 64)
        self.mute_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: #ffaa0022;
                border-radius: 8px;
            }
        """
        )
        self.mute_button.setToolTip("Audio Enabled")
        self.mute_button.clicked.connect(self.toggle_mute)

        header.addWidget(logo_button)
        header.addStretch()
        header.addWidget(settings_btn)
        header.addSpacing(20)
        header.addWidget(logs_btn)
        header.addStretch()
        header.addWidget(self.mute_button)

        layout.addLayout(header)

        # Main Action Buttons
        body_layout = QVBoxLayout()
        body_layout.setAlignment(Qt.AlignCenter)

        button_style = """
            QPushButton {
                background-color: #202020;
                color: #ffffff;
                border: 2px solid #ffaa00;
                border-radius: 10px;
                padding: 14px 40px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #333333;
            }
        """

        hide_btn = QPushButton("Hide Data")
        hide_btn.setStyleSheet(button_style)
        hide_btn.clicked.connect(lambda: self.central_stack.setCurrentIndex(1))

        unhide_btn = QPushButton("Unhide Data")
        unhide_btn.setStyleSheet(button_style)
        unhide_btn.clicked.connect(lambda: self.central_stack.setCurrentIndex(2))

        body_layout.addWidget(hide_btn)
        body_layout.addSpacing(20)
        body_layout.addWidget(unhide_btn)

        layout.addLayout(body_layout)

        # Footer
        footer = QHBoxLayout()
        footer.setContentsMargins(20, 10, 20, 20)

        tutorial_btn = QPushButton()
        tutorial_btn.setIcon(QIcon("assets/tutorial.png"))
        tutorial_btn.setIconSize(QSize(48, 48))
        tutorial_btn.setFixedSize(56, 56)
        tutorial_btn.setStyleSheet("background-color: transparent; border: none;")
        tutorial_btn.setToolTip("How to use Rygelock")

        footer.addWidget(tutorial_btn)
        footer.addStretch()

        layout.addLayout(footer)

        main_menu.setLayout(layout)
        # Add main_menu to the stack at index 0
        self.central_stack.addWidget(main_menu)

    def toggle_mute(self):
        self.is_muted = not self.is_muted
        icon_path = "assets/disable.png" if self.is_muted else "assets/audio.png"
        tooltip_text = "Audio Muted" if self.is_muted else "Audio Enabled"
        self.mute_button.setIcon(QIcon(icon_path))
        self.mute_button.setToolTip(tooltip_text)

    def init_embed_menu(self):
        self.embed_widget = EmbedWidget()
        # Add embed_widget to the stack at index 1
        self.central_stack.addWidget(self.embed_widget)

    def init_extract_menu(self):
        self.extract_widget = ExtractWidget()
        # Add extract_widget to the stack at index 2
        self.central_stack.addWidget(self.extract_widget)

    def init_settings_menu(self):
        self.settings_widget = SettingsWidget()
        # Connect the settings_closed signal to our new method
        self.settings_widget.settings_closed.connect(self.return_to_main_menu_from_settings)
        # Add settings_widget to the stack at index 3
        self.central_stack.addWidget(self.settings_widget)

    def return_to_main_menu_from_settings(self):
        """
        Slot to be called when the settings_closed signal is emitted from SettingsWidget.
        Switches the QStackedWidget back to the main menu (index 0).
        """
        print("Returning to main menu from settings.")
        self.central_stack.setCurrentIndex(0) # Assuming main menu is at index 0
        # If you applied theme changes or audio settings, you might want to refresh the UI here
        # For example: self.apply_current_theme() or self.update_audio_status()