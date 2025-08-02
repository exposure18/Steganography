# utils/file_validator.py — Validate carrier/payload file formats for Rygelock

import os

SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}
SUPPORTED_AUDIO_EXTENSIONS = {".wav", ".flac", ".aiff", ".aif", ".ogg"}
SUPPORTED_VIDEO_EXTENSIONS = {".avi", ".mp4", ".mkv", ".ts"}
SUPPORTED_MISC_EXTENSIONS  = {".txt", ".pdf", ".zip"}  # for payloads mostly

ALL_SUPPORTED = SUPPORTED_IMAGE_EXTENSIONS | SUPPORTED_AUDIO_EXTENSIONS | SUPPORTED_VIDEO_EXTENSIONS | SUPPORTED_MISC_EXTENSIONS

def is_supported_file(filepath):
    """
    Check if the file extension is one of the supported formats.
    """
    ext = os.path.splitext(filepath)[1].lower()
    return ext in ALL_SUPPORTED

def is_carrier_file(filepath):
    """Carrier files are typically image/audio/video only."""
    ext = os.path.splitext(filepath)[1].lower()
    return ext in (SUPPORTED_IMAGE_EXTENSIONS | SUPPORTED_AUDIO_EXTENSIONS | SUPPORTED_VIDEO_EXTENSIONS)

def is_payload_file(filepath):
    """Payloads can be text, images, small media, PDFs, archives, etc."""
    ext = os.path.splitext(filepath)[1].lower()
    return ext in ALL_SUPPORTED

def get_file_type(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    if ext in SUPPORTED_IMAGE_EXTENSIONS:
        return "image"
    elif ext in SUPPORTED_AUDIO_EXTENSIONS:
        return "audio"
    elif ext in SUPPORTED_VIDEO_EXTENSIONS:
        return "video"
    elif ext in SUPPORTED_MISC_EXTENSIONS:
        return "misc"
    return "unknown"

def apply_data_whitening(data: bytes) -> bytes:
    key = 0xA5  # XOR mask
    return bytes(b ^ key for b in data)

def apply_data_dewhitening(data: bytes) -> bytes:
    key = 0xA5  # Same XOR mask
    return bytes(b ^ key for b in data)