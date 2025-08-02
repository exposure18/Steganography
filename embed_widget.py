import os
from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QTextEdit, QLineEdit, QFileDialog,
    QVBoxLayout, QHBoxLayout, QGridLayout, QCheckBox, QTableWidget,
    QTableWidgetItem, QAbstractItemView, QMessageBox, QRadioButton, QButtonGroup, QSizePolicy, QGroupBox, QComboBox
)
from PyQt5.QtGui import QPixmap, QIcon, QFont
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from core.algorithm import detect_algorithm
from core.steg_engine import embed_files
# Removed: from core.deception_mech import prepare_fake_output
from utils.config import get_output_dir
from utils.file_validator import apply_data_whitening
from ui.embed_progress_popup import EmbedProgressPopup
from ui.result_viewer import ResultViewer

SUPPORTED_CARRIER_EXTENSIONS = [".png", ".jpg", ".bmp", ".tiff", ".webp", ".wav", ".flac", ".aiff", ".mp4", ".mkv",
                                ".avi", ".mp3"]


class EmbedWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        header_layout = QHBoxLayout()
        self.back_btn = QPushButton("🔙 Back")
        self.back_btn.setFixedWidth(150)
        self.back_btn.setToolTip("Return to the main menu")
        self.back_btn.clicked.connect(self.handle_back)
        header_layout.addWidget(self.back_btn)

        supported_label = QLabel("Supported: PNG, JPG, MP4, MP3")
        supported_label.setStyleSheet("color: orange; font-style: italic;")
        header_layout.addWidget(supported_label)

        header_layout.addStretch()
        reset_btn = QPushButton()
        reset_btn.setIcon(QIcon(QPixmap("assets/reset.png")))
        reset_btn.setToolTip("Reset all fields")
        reset_btn.clicked.connect(self.reset_all_fields)
        header_layout.addWidget(reset_btn)

        layout.addLayout(header_layout)

        grid = QGridLayout()
        carrier_label = QLabel("Carrier File(s)")
        carrier_label.setToolTip("Files that will carry your hidden data")
        self.carrier_table = QTableWidget(0, 1)
        self.carrier_table.setHorizontalHeaderLabels(["File Path"])
        self.carrier_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.carrier_table.horizontalHeader().setStretchLastSection(True)
        self.carrier_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        add_carrier_btn = QPushButton("Add Carrier File")
        add_carrier_btn.setToolTip("Upload a file to hide data into")
        add_carrier_btn.clicked.connect(self.add_carrier_file)

        grid.addWidget(carrier_label, 0, 0)
        grid.addWidget(self.carrier_table, 1, 0)
        grid.addWidget(add_carrier_btn, 2, 0)

        payload_label = QLabel("Payload File(s)")
        payload_label.setToolTip("Files you want to hide inside the carrier")
        self.payload_display = QTextEdit()
        self.payload_display.setReadOnly(True)
        self.payload_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        add_payload_btn = QPushButton("Add Payload File")
        add_payload_btn.setToolTip("Browse and add one or more payload files")
        add_payload_btn.clicked.connect(self.add_payload_file)

        grid.addWidget(payload_label, 0, 1)
        grid.addWidget(self.payload_display, 1, 1)
        grid.addWidget(add_payload_btn, 2, 1)

        layout.addLayout(grid)

        form_grid = QGridLayout()

        encryption_groupbox = QGroupBox("Encryption & Layers") # Keeping 'Layers' in title for now, but functionality is gone
        encryption_col = QVBoxLayout(spacing=3)
        encryption_label = QLabel("Encryption (Optional)")
        encryption_label.setFont(QFont("Segoe UI", 10, QFont.Bold))

        self.encryption_none = QRadioButton("None")
        self.encryption_aes = QRadioButton("AES")
        self.encryption_des = QRadioButton("Blowfish")
        self.encryption_fernet = QRadioButton("Fernet")
        self.encryption_none.setChecked(True)
        self.encryption_group = QButtonGroup()
        for btn in [self.encryption_none, self.encryption_aes, self.encryption_des, self.encryption_fernet]:
            self.encryption_group.addButton(btn)
        self.encryption_group.buttonClicked.connect(self.toggle_encryption_password)

        self.enc_password_input = QLineEdit()
        self.enc_password_input.setPlaceholderText("Encryption password (optional)")
        self.enc_password_input.setEchoMode(QLineEdit.Password)  # Mask password input
        self.enc_password_input.setEnabled(False)  # Initially disabled
        self.enc_password_input.setToolTip("Used to decrypt payloads if encryption is selected")
        # Connect textChanged signal to validation
        self.enc_password_input.textChanged.connect(self.validate_embedding_inputs)

        # --- NEW: Password Warning Label ---
        self.password_warning_label = QLabel("A password is required for selected encryption.")
        self.password_warning_label.setStyleSheet("color: #FF6347; font-weight: bold;")  # Tomato red for warning
        self.password_warning_label.setWordWrap(True)
        self.password_warning_label.hide()  # Hidden by default
        # --- END NEW ---

        self.generate_key_checkbox = QCheckBox("Generate Key")
        self.generate_key_checkbox.setToolTip("Generate a unique key file for unlocking")
        self.masking_checkbox = QCheckBox("Enable Masking")
        self.masking_checkbox.setToolTip("Enable obfuscation to disguise payload content")

        # Removed: Matryoshka Layer widgets
        # matryoshka_label = QLabel("Matryoshka Layer")
        # self.matryoshka_combo = QComboBox()
        # self.matryoshka_combo.addItems(["None", "1x", "2x", "3x"])
        # self.matryoshka_combo.setToolTip("Apply recursive steganography layers")

        # Updated loop to remove matryoshka widgets
        for w in [encryption_label, self.encryption_none, self.encryption_aes, self.encryption_des,
                  self.encryption_fernet,
                  self.enc_password_input, self.password_warning_label,
                  self.generate_key_checkbox, self.masking_checkbox]:
            encryption_col.addWidget(w)
        encryption_groupbox.setLayout(encryption_col)

        # Removed: Deception Groupbox entirely
        # deception_groupbox = QGroupBox("Deception & Message")
        # deception_col = QVBoxLayout(spacing=4)
        # deception_label = QLabel("Deception Mechanism")
        # self.fake_payload_display = QTextEdit()
        # self.fake_payload_display.setReadOnly(True)
        # self.fake_payload_display.setToolTip("Optional decoy files to mislead attackers")
        # add_fake_payload_btn = QPushButton("Add Fake Payload")
        # add_fake_payload_btn.setToolTip("Browse and select a fake file")
        # add_fake_payload_btn.clicked.connect(self.add_fake_payload)
        # self.fake_password_input = QLineEdit()
        # self.fake_password_input.setPlaceholderText("Fake password (optional)")
        # self.fake_password_input.setEchoMode(QLineEdit.Password)
        # self.fake_password_input.setToolTip("Password used to reveal fake data")
        # self.generate_fake_key_checkbox = QCheckBox("Generate Fake Key")
        # self.generate_fake_key_checkbox.setToolTip("Create a fake key file for decoy reveal")
        # for w in [deception_label, self.fake_payload_display, add_fake_payload_btn,
        #           self.fake_password_input, self.generate_fake_key_checkbox]:
        #     deception_col.addWidget(w)
        # deception_groupbox.setLayout(deception_col)

        # Updated form_grid to remove deception_groupbox
        form_grid.addWidget(encryption_groupbox, 0, 0)
        # Removed: form_grid.addWidget(deception_groupbox, 0, 1)
        layout.addLayout(form_grid)

        self.start_btn = QPushButton("Start Hiding")  # Store reference to the button
        self.start_btn.setToolTip("Start the steganography process with selected options")
        self.start_btn.clicked.connect(self.start_embedding)
        layout.addWidget(self.start_btn, alignment=Qt.AlignCenter)

        self.back_btn.setFocus()

        # Initialize the password field state based on default selection ("None")
        self.toggle_encryption_password()
        # Initial validation when the widget is created
        self.validate_embedding_inputs()

    def handle_back(self):
        parent = self.parent()
        while parent is not None:
            if hasattr(parent, 'setCurrentIndex'):
                parent.setCurrentIndex(0)
                return
            parent = parent.parent()

    def toggle_encryption_password(self):
        selected = self.encryption_group.checkedButton().text()
        if selected == "None":
            self.enc_password_input.clear()
            self.enc_password_input.setEnabled(False)
            self.enc_password_input.setPlaceholderText("No password needed")
            self.password_warning_label.hide()
            self.password_warning_label.setText("")
        else:
            self.enc_password_input.setEnabled(True)
            self.enc_password_input.setPlaceholderText("Encryption password")
            self.password_warning_label.setText(f"A password is required for {selected} encryption.")
            self.password_warning_label.show()

        # Also, update the state of the start button based on validation
        self.validate_embedding_inputs()

    def reset_all_fields(self):
        self.carrier_table.setRowCount(0)
        self.payload_display.clear()
        # Removed: self.fake_payload_display.clear()
        # Removed: self.fake_password_input.clear()
        self.enc_password_input.clear()
        self.encryption_none.setChecked(True)
        self.generate_key_checkbox.setChecked(False)
        # Removed: self.generate_fake_key_checkbox.setChecked(False)
        self.masking_checkbox.setChecked(False)
        # Removed: self.matryoshka_combo.setCurrentIndex(0)
        self.back_btn.setFocus()
        self.toggle_encryption_password()  # Reset password field state
        self.validate_embedding_inputs()  # Ensure button state is updated on reset

    def add_carrier_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Carrier File")
        if file_path:
            ext = os.path.splitext(file_path)[1].lower()
            if ext not in SUPPORTED_CARRIER_EXTENSIONS:
                QMessageBox.warning(self, "Unsupported File", "This file type is not supported as a carrier file.")
                return
            for row in range(self.carrier_table.rowCount()):
                if self.carrier_table.item(row, 0).text() == file_path:
                    QMessageBox.warning(self, "Duplicate File", "This carrier file is already added.")
                    return
            row = self.carrier_table.rowCount()
            self.carrier_table.insertRow(row)
            self.carrier_table.setItem(row, 0, QTableWidgetItem(file_path))
            self.validate_embedding_inputs()  # Validate after adding carrier

    def add_payload_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Payload File")
        if file:
            self.payload_display.append(file)
            self.validate_embedding_inputs()  # Validate after adding payload

    # Removed: add_fake_payload method
    # def add_fake_payload(self):
    #     file, _ = QFileDialog.getOpenFileName(self, "Select Fake Payload File")
    #     if file:
    #         self.fake_payload_display.append(file)
    #         self.validate_embedding_inputs()

    def validate_embedding_inputs(self):
        """
        Validates inputs and enables/disables the Start Hiding button.
        """
        carriers_exist = self.carrier_table.rowCount() > 0
        payloads_exist = bool(self.payload_display.toPlainText().strip())

        selected_encryption = self.encryption_group.checkedButton().text()
        password_provided = bool(self.enc_password_input.text().strip())

        # Condition 1: Must have carriers and payloads
        if not carriers_exist or not payloads_exist:
            self.start_btn.setEnabled(False)
            return

        # Condition 2: If encryption is selected, password must be provided
        if selected_encryption != "None" and not password_provided:
            self.start_btn.setEnabled(False)
            return

        # If all conditions pass, enable the button
        self.start_btn.setEnabled(True)

    def start_embedding(self):
        # Re-run validation just before starting to catch any last-minute changes
        self.validate_embedding_inputs()
        if not self.start_btn.isEnabled():
            QMessageBox.warning(self, "Input Error",
                                "Please ensure all required fields are filled correctly (e.g., add carrier/payload, or provide password for encryption).")
            return

        carriers = []
        for row in range(self.carrier_table.rowCount()):
            filepath = self.carrier_table.item(row, 0).text()
            algorithm = detect_algorithm(filepath) or "default"
            carriers.append({"file": filepath, "algorithm": algorithm})

        payloads = [line.strip() for line in self.payload_display.toPlainText().splitlines() if line.strip()]

        # Removed: fake_payloads, fake_password, generate_fake_key
        # fake_payloads = [line.strip() for line in self.fake_payload_display.toPlainText().splitlines() if line.strip()]
        # fake_password = self.fake_password_input.text().strip()

        # Get password, ensure it's None if empty string
        password = self.enc_password_input.text().strip()
        if not password:  # Convert empty string to None
            password = None

        if not carriers:
            QMessageBox.warning(self, "Missing Carrier", "Please add at least one carrier file.")
            return
        if not payloads:
            QMessageBox.warning(self, "Missing Payload", "Please add a payload file.")
            return

        config = {
            "carriers": carriers,
            "payloads": payloads,
            "encryption": self.encryption_group.checkedButton().text(),
            "password": password,
            "generate_key": self.generate_key_checkbox.isChecked(),
            "masking": self.masking_checkbox.isChecked(),
            # Removed: "matryoshka": self.matryoshka_combo.currentText(),
            # Removed: "fake_payloads": fake_payloads,
            # Removed: "fake_password": fake_password,
            # Removed: "generate_fake_key": self.generate_fake_key_checkbox.isChecked(),
            "output_dir": get_output_dir()
        }

        # Removed: prepare_fake_output call
        # if config["fake_payloads"] or config["generate_fake_key"]:
        #     prepare_fake_output(config)

        self.progress_popup = EmbedProgressPopup()
        self.progress_popup.show()

        class WorkerThread(QThread):
            progress = pyqtSignal(int)
            done = pyqtSignal(dict)

            def run(self_):
                try:
                    result = embed_files(config, self_.progress.emit)
                except Exception as e:
                    result = {"status": "error", "message": str(e)}
                self_.done.emit(result)

        self.worker = WorkerThread()
        self.worker.progress.connect(self.progress_popup.update_progress)
        self.worker.done.connect(self.progress_popup.close_and_show_result)
        self.worker.start()