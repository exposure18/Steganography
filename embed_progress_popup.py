from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QMessageBox, QApplication
from PyQt5.QtCore import Qt

from ui.result_viewer import ResultViewer

class EmbedProgressPopup(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Embedding In Progress")
        self.setFixedSize(350, 120)
        self.setStyleSheet("background-color: #1e1e1e; color: white;")

        layout = QVBoxLayout()

        self.status_label = QLabel("Please wait while embedding is in progress...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 14px;")

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #444;
                border-radius: 5px;
                text-align: center;
                background-color: #2d2d2d;
            }
            QProgressBar::chunk {
                background-color: #ffaa00;
                width: 20px;
            }
        """)

        self.percent_label = QLabel("Progress: 0%")
        self.percent_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.percent_label)

        self.setLayout(layout)
        self.setWindowModality(Qt.ApplicationModal)

    def update_progress(self, value):
        self.progress_bar.setValue(value)
        self.percent_label.setText(f"Progress: {value}%")

    def close_and_show_result(self, result):
        self.close()
        if result.get("status") == "Failed":
            error_text = "<br>".join(result.get("errors", ["An unknown error occurred."]))
            QMessageBox.critical(None, "Embedding Failed", f"<span style='color: orange;'>{error_text}</span>")
        else:
            success_text = "<span style='color: orange;'>Data successfully hidden in carrier file(s).</span>"
            QMessageBox.information(None, "Embedding Complete", success_text)

        #After closing popup, return to main menu
        app = QApplication.instance()
        for widget in app.topLevelWidgets():
            if hasattr(widget, 'central_stack'):
                widget.central_stack.setCurrentIndex(0)

