import json
import random
import hashlib
from datetime import datetime

# Custom 2-character encoding dictionary (partial sample shown)
KEY_DICT = {
    'a': 'xQ', 'b': 't7', 'c': 'L9', 'd': 'n1', 'e': 'w2', 'f': 'b3', 'g': 'o4', 'h': 'r5',
    'i': 'v6', 'j': 'y7', 'k': 's8', 'l': 'm9', 'm': 'c0', 'n': 'd1', 'o': 'f2', 'p': 'g3',
    'q': 'h4', 'r': 'j5', 's': 'k6', 't': 'l7', 'u': 'z8', 'v': 'a9', 'w': 'e0', 'x': 'u1',
    'y': 'p2', 'z': 'q3', ' ': 'r4', '{': 's5', '}': 't6', '"': 'u7', ':': 'v8', ',': 'w9',
    'A': 'X1', 'B': 'T2', 'C': 'L3', 'D': 'N4', 'E': 'W5', 'F': 'B6', 'G': 'O7', 'H': 'R8',
    'I': 'V9', 'J': 'Y0', 'K': 'S1', 'L': 'M2', 'M': 'C3', 'N': 'D4', 'O': 'F5', 'P': 'G6',
    'Q': 'H7', 'R': 'J8', 'S': 'K9', 'T': 'L0', 'U': 'Z1', 'V': 'A2', 'W': 'E3', 'X': 'U4',
    'Y': 'P5', 'Z': 'Q6', '0': 'R7', '1': 'S8', '2': 'T9', '3': 'U0', '4': 'V1', '5': 'W2',
    '6': 'X3', '7': 'Y4', '8': 'Z5', '9': 'A6', '.': 'B7', '-': 'C8', '\n': 'NL'
}

REVERSE_KEY_DICT = {v: k for k, v in KEY_DICT.items()}


def generate_dict_checksum() -> str:
    """Generates a hash checksum of the dictionary for validation."""
    raw = ''.join(sorted(KEY_DICT.keys())) + ''.join(sorted(KEY_DICT.values()))
    return hashlib.sha256(raw.encode()).hexdigest()


def generate_salt(length=8) -> str:
    """Returns a random salt."""
    chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return ''.join(random.choice(chars) for _ in range(length))


def encode_key_metadata(metadata: dict) -> bytes:  # <<< Changed return type hint to bytes
    """
    Encodes the metadata dictionary into a custom-encoded string,
    appends a salt and checksum, and returns the result as bytes.
    """
    metadata = metadata.copy()
    metadata['salt'] = generate_salt()
    metadata['dict_checksum'] = generate_dict_checksum()

    json_str = json.dumps(metadata)
    encoded_str_parts = []
    for char in json_str:
        encoded_str_parts.append(KEY_DICT.get(char, char))  # Use .get() with default for unknown chars

    encoded_str = ''.join(encoded_str_parts)

    # CRITICAL: Encode the final string to bytes before returning
    return encoded_str.encode('utf-8')


def decode_key_metadata(encoded_bytes: bytes) -> dict:  # <<< Changed input type hint to bytes
    """
    Decodes the custom-encoded bytes back into a metadata dictionary.
    Performs a dictionary checksum validation.
    """
    encoded_str = encoded_bytes.decode('utf-8')  # <<< Decode bytes to string first

    i = 0
    decoded = ''
    while i < len(encoded_str):
        token = encoded_str[i:i + 2]
        char = REVERSE_KEY_DICT.get(token, '?')  # Use .get() with default for unknown tokens
        decoded += char
        i += 2

    try:
        obj = json.loads(decoded)
        if obj.get("dict_checksum") != generate_dict_checksum():
            raise ValueError("Dictionary mismatch! Key may be incompatible.")
        return obj
    except json.JSONDecodeError:
        raise ValueError("Failed to decode key. Possibly corrupted or invalid.")