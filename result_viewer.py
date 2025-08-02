# ui/result_viewer.py — Popup viewer for steganography results

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QTextEdit, QHBoxLayout, QApplication
from PyQt5.QtGui import QFont, QClipboard
from PyQt5.QtCore import Qt

class ResultViewer(QDialog):
    def __init__(self, result_summary: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Steganography Result")
        self.setMinimumSize(600, 500)
        self.setStyleSheet("background-color: #2c2c2c; color: white;")

        layout = QVBoxLayout()

        label = QLabel("Operation Summary")
        label.setFont(QFont("Arial", 14, QFont.Bold))
        label.setAlignment(Qt.AlignCenter)

        self.textbox = QTextEdit()
        self.textbox.setText(result_summary)
        self.textbox.setReadOnly(True)
        self.textbox.setStyleSheet("background-color: #1e1e1e; color: white; border: none;")
        self.textbox.setFont(QFont("Consolas", 11))

        button_layout = QHBoxLayout()
        self.copy_btn = QPushButton("Copy to Clipboard")
        self.copy_btn.clicked.connect(self.copy_to_clipboard)

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)

        button_layout.addWidget(self.copy_btn)
        button_layout.addWidget(self.close_btn)

        layout.addWidget(label)
        layout.addWidget(self.textbox)
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def copy_to_clipboard(self):
        clipboard: QClipboard = QApplication.clipboard()
        clipboard.setText(self.textbox.toPlainText())
