from Crypto.Cipher import AES, Blowfish
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2
from cryptography.fernet import Fernet, InvalidToken
import base64
import hashlib
import os # Added for os.urandom if needed for KDF salt, though PBKDF2 handles it

BLOCK_SIZE_AES = 16
BLOCK_SIZE_BLOWFISH = 8
PBKDF2_ITER = 100_000
SALT_SIZE = 16 # For salts directly managed by us (e.g., prepended to ciphertext)

# --- Helper function for Key Derivation ---
# This function will now incorporate `key_data` if provided.
def _derive_key_material(password: str, salt: bytes, key_data: bytes = None, dkLen: int = 32) -> bytes:
    """
    Derives a cryptographic key using PBKDF2, combining password and optional key_data.
    """
    password_bytes = password.encode('utf-8')
    if key_data:
        # Combine password and key_data for a stronger seed for PBKDF2
        # Use a consistent, non-reversible combination if key_data is binary.
        # For simplicity here, we concatenate, then hash, then use as part of PBKDF2 input.
        # A more robust approach might be to use key_data as a secret salt if applicable
        # or use a different KDF combining multiple secrets.
        # Given PBKDF2 takes password and salt, we'll combine them to make a 'super-password'.
        combined_password_seed = hashlib.sha256(password_bytes + key_data).digest()
    else:
        combined_password_seed = password_bytes

    # PBKDF2 returns the derived key (dkLen bytes long)
    # The 'salt' here is the random salt *for PBKDF2 itself*, not the `SALT_SIZE` from `key_data`.
    # PBKDF2 handles its internal salt generation if not explicitly given, but here we pass ours.
    return PBKDF2(combined_password_seed, salt, dkLen=dkLen, count=PBKDF2_ITER)

# --------------------------- AES ----------------------------
def encrypt_aes(data: bytes, password: str, key_data: bytes = None) -> bytes:
    salt = get_random_bytes(SALT_SIZE) # Salt for PBKDF2
    key = _derive_key_material(password, salt, key_data, dkLen=32) # AES key is 32 bytes for AES-256
    iv = get_random_bytes(BLOCK_SIZE_AES) # IV for CBC mode
    cipher = AES.new(key, AES.MODE_CBC, iv)
    # PKCS7 padding equivalent
    pad_len = BLOCK_SIZE_AES - len(data) % BLOCK_SIZE_AES
    data += bytes([pad_len]) * pad_len
    encrypted = cipher.encrypt(data)
    return salt + iv + encrypted # Prepend salt and IV to the ciphertext

def decrypt_aes(data: bytes, password: str, key_data: bytes = None) -> bytes:
    salt = data[:SALT_SIZE]
    iv = data[SALT_SIZE:SALT_SIZE + BLOCK_SIZE_AES]
    encrypted = data[SALT_SIZE + BLOCK_SIZE_AES:]
    key = _derive_key_material(password, salt, key_data, dkLen=32)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = cipher.decrypt(encrypted)
    # Unpad
    pad_len = decrypted[-1]
    # Check for valid padding length (important for integrity check)
    if not (1 <= pad_len <= BLOCK_SIZE_AES and decrypted[-pad_len:] == bytes([pad_len]) * pad_len):
        raise ValueError("Invalid padding detected during AES decryption. Possible incorrect password/key or corrupted data.")
    return decrypted[:-pad_len]

# ------------------------- Blowfish --------------------------
def encrypt_blowfish(data: bytes, password: str, key_data: bytes = None) -> bytes:
    salt = get_random_bytes(SALT_SIZE)
    # Blowfish key length can be variable (32-448 bits, i.e., 4-56 bytes)
    # Let's derive 56 bytes to provide maximum strength for Blowfish
    key = _derive_key_material(password, salt, key_data, dkLen=56)
    iv = get_random_bytes(BLOCK_SIZE_BLOWFISH)
    cipher = Blowfish.new(key, Blowfish.MODE_CBC, iv)
    # PKCS7 padding equivalent
    pad_len = BLOCK_SIZE_BLOWFISH - len(data) % BLOCK_SIZE_BLOWFISH
    data += bytes([pad_len]) * pad_len
    encrypted = cipher.encrypt(data)
    return salt + iv + encrypted

def decrypt_blowfish(data: bytes, password: str, key_data: bytes = None) -> bytes:
    salt = data[:SALT_SIZE]
    iv = data[SALT_SIZE:SALT_SIZE + BLOCK_SIZE_BLOWFISH]
    encrypted = data[SALT_SIZE + BLOCK_SIZE_BLOWFISH:]
    key = _derive_key_material(password, salt, key_data, dkLen=56)
    cipher = Blowfish.new(key, Blowfish.MODE_CBC, iv)
    decrypted = cipher.decrypt(encrypted)
    # Unpad
    pad_len = decrypted[-1]
    # Check for valid padding length
    if not (1 <= pad_len <= BLOCK_SIZE_BLOWFISH and decrypted[-pad_len:] == bytes([pad_len]) * pad_len):
        raise ValueError("Invalid padding detected during Blowfish decryption. Possible incorrect password/key or corrupted data.")
    return decrypted[:-pad_len]

# -------------------------- Fernet ---------------------------
def encrypt_fernet(data: bytes, password: str, key_data: bytes = None) -> bytes:
    salt = get_random_bytes(SALT_SIZE)
    # Fernet key needs to be 32 URL-safe base64-encoded bytes
    key_material = _derive_key_material(password, salt, key_data, dkLen=32)
    fernet_key = base64.urlsafe_b64encode(key_material)
    f = Fernet(fernet_key)
    encrypted = f.encrypt(data)
    return salt + encrypted # Prepend salt to the Fernet token

def decrypt_fernet(data: bytes, password: str, key_data: bytes = None) -> bytes:
    salt = data[:SALT_SIZE]
    encrypted = data[SALT_SIZE:]
    key_material = _derive_key_material(password, salt, key_data, dkLen=32)
    fernet_key = base64.urlsafe_b64encode(key_material)
    f = Fernet(fernet_key)
    return f.decrypt(encrypted) # Fernet handles its own integrity/padding internally

# ---------------------- Dispatcher ---------------------------
# These functions are the main entry points for your UI
def encrypt_file(data: bytes, algorithm: str, password: str, key_data: bytes = None) -> bytes:
    """
    Encrypts data using the specified algorithm, password, and optional key_data.
    """
    if not password: # Ensure password is not empty for encryption
        raise ValueError("Password cannot be empty for encryption.")

    if algorithm == "AES":
        return encrypt_aes(data, password, key_data)
    elif algorithm == "Fernet":
        return encrypt_fernet(data, password, key_data)
    elif algorithm == "Blowfish":
        return encrypt_blowfish(data, password, key_data)
    else:
        raise ValueError(f"Unsupported encryption algorithm: {algorithm}")

def decrypt_file(data: bytes, password: str, algorithm: str, key_data: bytes = None) -> bytes:
    """
    Decrypts data using the specified algorithm, password, and optional key_data.
    Raises ValueError for decryption failures (wrong password/key, corruption).
    """
    if not password: # Ensure password is not empty for decryption
        raise ValueError("Password cannot be empty for decryption.")

    try:
        if algorithm == "AES":
            return decrypt_aes(data, password, key_data)
        elif algorithm == "Fernet":
            return decrypt_fernet(data, password, key_data)
        elif algorithm == "Blowfish":
            return decrypt_blowfish(data, password, key_data)
        else:
            raise ValueError(f"Unsupported decryption algorithm: {algorithm}")
    except (ValueError, InvalidToken) as e:
        # Re-raise with a more generic message for UI, but preserve original for debugging
        raise ValueError(f"Decryption failed. Incorrect password/key or corrupted data. Original error: {e}")

# -------------------- Optional Masking ------------------------
# This masking function is independent of encryption key derivation.
# It acts as an additional obfuscation layer.
def apply_masking(data: bytes) -> bytes:
    """
    Applies a simple XOR mask for obfuscation. This is symmetric; applying it twice
    with the same mask reveals the original data. The mask is derived from the
    first 32 bytes of the input data.
    """
    if len(data) < 32: # Ensure enough data to derive a mask
        # If data is too short, pad it or use a simpler mask
        # For simplicity, let's just use the whole data as seed if too short
        mask_seed = data
    else:
        mask_seed = data[:32]

    # Derive a repeatable mask from a segment of the data
    # NOTE: This makes masking reversible. If you want truly random masking,
    # the mask itself would need to be embedded or known via other means.
    mask = hashlib.sha256(mask_seed).digest() # 32-byte mask

    # XOR each byte with the repeating mask
    return bytes(b ^ mask[i % len(mask)] for i, b in enumerate(data))

# You might want an explicit de-masking function if the masking
# isn't simply reversible by applying the same function.
# For this current apply_masking, applying it again would reverse it:
def apply_demasking(data: bytes) -> bytes:
    """
    Reverses the effect of apply_masking, assuming the same mask derivation.
    """
    return apply_masking(data) # It's its own inverse in this case