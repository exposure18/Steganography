# ui/reveal_widget.py — GUI for revealing logs based on password

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextEdit, QLineEdit,
    QPushButton, QMessageBox, QHBoxLayout
)
from core.logger import load_logs, clear_logs

class RevealWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.info_label = QLabel("Enter password to view logs:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)

        button_layout = QHBoxLayout()
        self.reveal_button = QPushButton("Reveal Logs")
        self.reveal_button.clicked.connect(self.reveal_logs)

        self.clear_real_button = QPushButton("Clear Real Logs")
        self.clear_real_button.clicked.connect(lambda: self.clear_logs(True))

        self.clear_fake_button = QPushButton("Clear Decoy Logs")
        self.clear_fake_button.clicked.connect(lambda: self.clear_logs(False))

        button_layout.addWidget(self.reveal_button)
        button_layout.addWidget(self.clear_real_button)
        button_layout.addWidget(self.clear_fake_button)

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)

        layout.addWidget(self.info_label)
        layout.addWidget(self.password_input)
        layout.addLayout(button_layout)
        layout.addWidget(self.log_view)

        self.setLayout(layout)

    def reveal_logs(self):
        password = self.password_input.text()
        success, content = load_logs(password)

        if success:
            self.log_view.setPlainText(content)
        else:
            QMessageBox.warning(self, "Access Denied", content)

    def clear_logs(self, real=True):
        clear_logs(real)
        msg = "Real logs cleared." if real else "Decoy logs cleared."
        QMessageBox.information(self, "Logs Cleared", msg)
