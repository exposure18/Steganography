# core/logger.py — Logging logic with real/fake split and Logger class

import os
import datetime
import hashlib

# Paths to log storage
REAL_LOG_FILE = "logs/real_logs.txt"
FAKE_LOG_FILE = "logs/fake_logs.txt"

# Default password hashes (replace later with secure storage)
REAL_LOG_PASSWORD_HASH = hashlib.sha256("real_access".encode()).hexdigest()
FAKE_LOG_PASSWORD_HASH = hashlib.sha256("decoy_access".encode()).hexdigest()

class Logger:
    def __init__(self):
        self._ensure_log_dirs()

    def _ensure_log_dirs(self):
        os.makedirs(os.path.dirname(REAL_LOG_FILE), exist_ok=True)
        os.makedirs(os.path.dirname(FAKE_LOG_FILE), exist_ok=True)

    def log_real(self, event_type, message):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] [{event_type.upper()}] {message}"
        with open(REAL_LOG_FILE, "a") as f:
            f.write(entry + "\n")

    def log_fake(self, message):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] [DECOY] {message}"
        with open(FAKE_LOG_FILE, "a") as f:
            f.write(entry + "\n")

    def get_real_logs(self):
        try:
            with open(REAL_LOG_FILE, "r") as f:
                return f.readlines()
        except FileNotFoundError:
            return ["No real logs found."]

    def get_fake_logs(self):
        try:
            with open(FAKE_LOG_FILE, "r") as f:
                return f.readlines()
        except FileNotFoundError:
            return ["No decoy logs found."]

    def clear_real_logs(self):
        open(REAL_LOG_FILE, "w").close()

    def clear_fake_logs(self):
        open(FAKE_LOG_FILE, "w").close()

    def verify_password(self, password):
        entered_hash = hashlib.sha256(password.encode()).hexdigest()
        if entered_hash == REAL_LOG_PASSWORD_HASH:
            return True
        if entered_hash == FAKE_LOG_PASSWORD_HASH:
            return True
        return False
