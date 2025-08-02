# ui/log_widget.py — Log Manager for Rygelock

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QPushButton,
    QHBoxLayout, QInputDialog, QMessageBox, QFileDialog
)
from core.logger import Logger

class LogWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.logger = Logger()
        self.fake_mode = True  # Start with fake logs
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.log_list = QListWidget()
        layout.addWidget(self.log_list)

        # Buttons
        button_layout = QHBoxLayout()
        self.toggle_button = QPushButton("Switch to Real Logs")
        self.clear_button = QPushButton("Clear Logs")
        self.export_button = QPushButton("Export Logs")

        self.toggle_button.clicked.connect(self.toggle_log_mode)
        self.clear_button.clicked.connect(self.clear_logs)
        self.export_button.clicked.connect(self.export_logs)

        button_layout.addWidget(self.toggle_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.export_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        self.load_logs()

    def load_logs(self):
        self.log_list.clear()
        logs = self.logger.get_fake_logs() if self.fake_mode else self.logger.get_real_logs()
        self.log_list.addItems(logs)

    def toggle_log_mode(self):
        password, ok = QInputDialog.getText(self, "Authentication", "Enter password:", echo=QInputDialog.Password)
        if ok and self.logger.verify_password(password):
            self.fake_mode = not self.fake_mode
            self.toggle_button.setText("Switch to Fake Logs" if not self.fake_mode else "Switch to Real Logs")
            self.load_logs()
        else:
            QMessageBox.warning(self, "Access Denied", "Incorrect password.")

    def clear_logs(self):
        password, ok = QInputDialog.getText(self, "Confirm Deletion", "Enter password to clear logs:", echo=QInputDialog.Password)
        if ok and self.logger.verify_password(password):
            if self.fake_mode:
                self.logger.clear_fake_logs()
            else:
                self.logger.clear_real_logs()
            self.load_logs()
        else:
            QMessageBox.warning(self, "Access Denied", "Incorrect password.")

    def export_logs(self):
        try:
            path, _ = QFileDialog.getSaveFileName(self, "Export Logs", filter="Text Files (*.txt)")
            if path:
                logs = self.logger.get_fake_logs() if self.fake_mode else self.logger.get_real_logs()
                with open(path, "w") as file:
                    for line in logs:
                        file.write(f"{line}\n")
                QMessageBox.information(self, "Export Successful", "Logs exported successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))
