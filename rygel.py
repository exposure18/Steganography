
# rygel.py — Entry point for Rygelock

import sys
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow
from core.style_sheet import glass_style

if __name__ == '__main__':
    app = QApplication(sys.argv)

    app.setStyleSheet(glass_style)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())
