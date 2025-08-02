import os
from core.algorithm_stubs import (
    run_simple_jpg_steg,
    mp3_steg,
    mp4_steg
)

ALGORITHM_FN_MAP = {
    "jpg": run_simple_jpg_steg,
    "jpeg": run_simple_jpg_steg,
    "png": run_simple_jpg_steg,
    "mp3": mp3_steg,
    "mp4": mp4_steg
}

ALGORITHM_MAP = {
    ".png": "s-uniward",
    ".jpg": "wow",
    ".jpeg": "wow",
    ".bmp": "stc",
    ".tiff": "hugo",
    ".webp": "mipod",
    ".wav": "stc",
    ".flac": "mipod",
    ".aiff": "mvg",
    ".mp4": "mp4",
    ".mkv": "synch",
    ".avi": "synch",
    ".mp3": "mp3"
}

def detect_algorithm(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    return ALGORITHM_MAP.get(ext, None)

def get_supported_algorithms():
    return sorted(set(ALGORITHM_MAP.values()))

def is_extension_supported(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    return ext in ALGORITHM_MAP

def list_supported_extensions():
    return sorted(ALGORITHM_MAP.keys())

def route_algorithm(path):
    ext = os.path.splitext(path)[1].lower()
    algo_key = ext.lstrip('.')
    return ALGORITHM_FN_MAP.get(algo_key)

def stego_apply(carrier_path, payload, algorithm, output_path=None):
    fn = route_algorithm(carrier_path)
    if fn is None:
        raise ValueError(f"No stego function found for extension: {carrier_path}")

    if output_path is None:
        output_path = os.path.splitext(carrier_path)[0] + "_stego" + os.path.splitext(carrier_path)[1]

    print(f"[stego_apply] Running {fn.__name__} on {carrier_path} → {output_path}")
    if isinstance(payload, bytes):
        temp_payload_path = output_path + ".payload"
        with open(temp_payload_path, "wb") as f:
            f.write(payload)
        payload_path = temp_payload_path
    else:
        payload_path = payload

    try:
        result = fn(carrier_path, payload_path, output_path)
        if not os.path.exists(output_path):
            print(f"[ERROR] Output file not found after embedding: {output_path}")
        else:
            print(f"[OK] Stego file created: {output_path}")
        return result
    except Exception as e:
        print(f"[stego_apply ERROR] {e}")
        return None

def stego_extract(carrier_path, output_path=None):
    # Placeholder — to be implemented
    pass

