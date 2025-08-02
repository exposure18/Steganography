# utils/config.py — Configuration handler

import json
import os

CONFIG_FILE = "user_config.json"

DEFAULT_CONFIG = {
    "theme": "light",
    "audio": True,
    "decoy_logs": False
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return DEFAULT_CONFIG
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

def get_output_dir():
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    output_path = os.path.join(desktop, "Rygelock_Output")
    os.makedirs(output_path, exist_ok=True)
    return output_path