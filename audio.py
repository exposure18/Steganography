# utils/audio.py — Audio feedback module for Rygelock (mp3 version)

import os
import threading
from pathlib import Path
from pygame import mixer

# Initialize mixer once
def init_audio():
    try:
        mixer.init()
    except Exception as e:
        print("[Audio] Initialization failed:", e)

AUDIO_DIR = Path("assets/audio")

SOUNDS = {
    "success": AUDIO_DIR / "success.mp3",
    "fail": AUDIO_DIR / "fail.mp3",
    "progress": AUDIO_DIR / "progress.mp3",
    "chime": AUDIO_DIR / "chime.mp3",
}

def play_sound(tag):
    def worker():
        try:
            if tag in SOUNDS and SOUNDS[tag].exists():
                mixer.music.load(str(SOUNDS[tag]))
                mixer.music.play()
        except Exception as e:
            print(f"[Audio] Failed to play '{tag}':", e)

    threading.Thread(target=worker, daemon=True).start()

def stop_audio():
    mixer.music.stop()