# core/theme_manager.py — Handles theming and styles for Rygelock

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPalette, QColor

def apply_dark_theme(app: QApplication):
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(30, 30, 30))
    palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
    palette.setColor(QPalette.Base, QColor(45, 45, 45))
    palette.setColor(QPalette.AlternateBase, QColor(60, 60, 60))
    palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
    palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
    palette.setColor(QPalette.Text, QColor(255, 255, 255))
    palette.setColor(QPalette.Button, QColor(60, 60, 60))
    palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
    palette.setColor(QPalette.Highlight, QColor(85, 170, 255))
    palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))

    app.setPalette(palette)
    app.setStyleSheet(dark_stylesheet())

def apply_light_theme(app: QApplication):
    app.setPalette(QPalette())
    app.setStyleSheet(light_stylesheet())

def dark_stylesheet():
    return """
        QWidget {
            background-color: #1e1e1e;
            color: white;
            font-family: 'Segoe UI', sans-serif;
            font-size: 13px;
        }

        QPushButton {
            background-color: rgba(255, 255, 255, 0.05);
            border: 1px solid #555;
            border-radius: 12px;
            padding: 8px 16px;
        }

        QPushButton:hover {
            background-color: rgba(255, 255, 255, 0.10);
            box-shadow: 0 0 5px #00f0ff;
        }

        QLineEdit, QTextEdit {
            background-color: rgba(255, 255, 255, 0.08);
            border: 1px solid #555;
            border-radius: 8px;
            padding: 6px;
        }

        QTabWidget::pane {
            border: 0;
            background: transparent;
        }

        QTabBar::tab {
            background: transparent;
            padding: 8px;
        }

        QTabBar::tab:selected {
            border-bottom: 2px solid #00f0ff;
        }
    """

def light_stylesheet():
    return """
        QWidget {
            background-color: #ffffff;
            color: black;
            font-family: 'Segoe UI', sans-serif;
            font-size: 13px;
        }

        QPushButton {
            background-color: rgba(0, 0, 0, 0.05);
            border: 1px solid #aaa;
            border-radius: 12px;
            padding: 8px 16px;
        }

        QPushButton:hover {
            background-color: rgba(0, 0, 0, 0.10);
            box-shadow: 0 0 5px #007acc;
        }

        QLineEdit, QTextEdit {
            background-color: rgba(0, 0, 0, 0.05);
            border: 1px solid #aaa;
            border-radius: 8px;
            padding: 6px;
        }

        QTabBar::tab:selected {
            border-bottom: 2px solid #007acc;
        }
    """
