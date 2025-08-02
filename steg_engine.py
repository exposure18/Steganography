import os
import time
import hashlib
import json
import uuid
from datetime import datetime
from core.encryption import encrypt_file, decrypt_file, apply_masking
from core.algorithm import stego_apply, stego_extract
from utils.config import get_output_dir
from utils.file_validator import apply_data_whitening, apply_data_dewhitening
from utils.key_encoder import encode_key_metadata, generate_dict_checksum
from cryptography.fernet import InvalidToken

# --- Constants for Metadata/Tags ---
HEADER_MARKER = b"RYGELHDR\0"  # Unique marker for the metadata header


# --- Helper for Single-Layer Encryption/Masking (Matryoshka removed) ---
def apply_multilayer_encryption(data: bytes, encryption: str, password: str, masking: bool = False,
                                key_data: bytes = None) -> bytes:
    """
    Applies encryption and optional masking in a single layer.
    The key derivation for encryption (and use of key_data) is handled within core/encryption.py's encrypt_file.
    """
    data = encrypt_file(data, encryption, password, key_data=key_data)
    if masking:
        data = apply_masking(data)
    return data


# --- Embedding Function ---
def embed_files(config: dict, progress_callback) -> dict:
    """
    Embeds payload files into carrier files with specified encryption, masking,
    and generates keys if selected. (Matryoshka and Deception layers removed).
    """
    result = {
        "status": "Success",
        "embedded_files": [],
        "used_algorithms": set(),
        "key_generated": False,
        "encryption_used": config["encryption"] if config["encryption"] != "None" else None,
        "errors": []
    }

    try:
        output_dir = get_output_dir()
        os.makedirs(output_dir, exist_ok=True)

        all_payloads = config["payloads"][:]
        carriers = config["carriers"]
        assigned_pairs = []
        used_carriers = []

        # Pair payloads with suitable carriers based on size
        for payload in all_payloads:
            p_size = len(payload) if isinstance(payload, bytes) else os.path.getsize(payload)
            matched = False
            for item in carriers:
                c_path = item["file"]
                if c_path in used_carriers:
                    continue
                c_size = os.path.getsize(c_path)
                if c_size > p_size * 1.2:  # Carrier must be at least 20% larger than payload
                    assigned_pairs.append((item, payload))
                    used_carriers.append(c_path)
                    matched = True
                    break
            if not matched:
                raise ValueError(
                    f"No suitable carrier found for payload: {os.path.basename(payload) if not isinstance(payload, bytes) else 'bytes_payload'}")

        # Force single layer embedding as matryoshka is removed
        layers = 1
        total = len(assigned_pairs) # total progress is now just based on number of pairs
        current = 0

        # --- Generate Real Key Content EARLY if needed for encryption ---
        real_key_data_for_encryption = None
        if config["generate_key"]:
            carrier_names_for_key_hash = "_".join([os.path.basename(c["file"]) for c in config["carriers"]])
            timestamp_for_key_hash = datetime.now().isoformat()
            hash_input_for_key = (carrier_names_for_key_hash + timestamp_for_key_hash).encode("utf-8")
            hash_digest_for_key = hashlib.sha256(hash_input_for_key).hexdigest()

            key_metadata_content_dict = {
                "type": "genuine_key_metadata",
                "version": "RYG-1.0",
                "binding_info": carrier_names_for_key_hash,
                "timestamp": timestamp_for_key_hash,
                "hash_of_binding_info": hash_digest_for_key,
                "encryption_algo_used": config.get("encryption", "None"),
                "whitened_at_embed": config.get("masking", False)
            }
            real_key_data_for_encryption = encode_key_metadata(key_metadata_content_dict)

        # Process each assigned carrier-payload pair
        for idx, (item, payload) in enumerate(assigned_pairs):
            carrier = item["file"]
            algorithm = item["algorithm"]
            if algorithm == "Default":
                _, ext = os.path.splitext(carrier)
                # Assuming stego_apply is capable of returning the default algorithm based on extension if needed,
                # or that the 'algorithm' field from 'detect_algorithm' is sufficient.
                # If stego_apply expects the actual algorithm function, this logic might need adjustment.
                # For now, keeping as is, assuming 'algorithm' value is sufficient.
                pass # Already set by detect_algorithm or remains "Default"

            result["used_algorithms"].add(algorithm)

            if isinstance(payload, bytes):
                payload_data = payload
            else:
                with open(payload, "rb") as f:
                    payload_data = f.read()

            metadata = {
                "type": "genuine",
                "version": "RYG-1.0",
                "timestamp": datetime.now().isoformat(),
                # "matryoshka_layers": layers, # Removed
                "encryption": config["encryption"],
                "generate_key_used": config["generate_key"],
                "whitened": False,
                "encryption_masking_applied": config["masking"]
            }

            if config["encryption"] != "None" and config["password"]:
                payload_data = apply_multilayer_encryption(
                    payload_data,
                    config["encryption"],
                    config["password"],
                    masking=config["masking"],
                    key_data=real_key_data_for_encryption
                )

            if config["masking"]:
                payload_data = apply_data_whitening(payload_data)
                metadata["whitened"] = True

            metadata_block = HEADER_MARKER + json.dumps(metadata).encode("utf-8") + b"\0"
            full_payload = metadata_block + payload_data

            temp_payload_path = os.path.join(output_dir, f"temp_payload_{idx}_{uuid.uuid4().hex}.bin")
            with open(temp_payload_path, "wb") as temp:
                temp.write(full_payload)

            current_carrier = carrier
            # The loop for layers now runs only once because layers is set to 1
            for layer in range(layers):
                original_name = os.path.basename(current_carrier)
                steg_output = os.path.join(output_dir, f"stego_layer{layer + 1}_{idx}_{original_name}")
                stego_apply(current_carrier, temp_payload_path, algorithm, output_path=steg_output)

                if not os.path.exists(steg_output):
                    raise FileNotFoundError(f"[Layer {layer + 1}] Stego file not created: {steg_output}")

                current_carrier = steg_output
                current += 1
                progress_callback(int((current / total) * 100))
                time.sleep(0.05)

            final_output_name = os.path.join(output_dir, os.path.basename(carrier))
            if os.path.exists(final_output_name):
                base, ext = os.path.splitext(final_output_name)
                final_output_name = f"{base}_embedded_{uuid.uuid4().hex[:4]}{ext}"
            os.rename(current_carrier, final_output_name)
            result["embedded_files"].append(os.path.basename(final_output_name))

        # --- Write Real Key File (if generated) ---
        if config["generate_key"]:
            key_path = os.path.join(output_dir, "real_key.key")
            with open(key_path, "wb") as f:
                f.write(real_key_data_for_encryption)
            result["key_generated"] = True

        # --- Removed: Embed Fake Payloads section ---
        # No more deception logic here

    except Exception as e:
        result["status"] = "Failed"
        result["errors"].append(str(e))
        print(f"Error during embedding: {e}")

    finally:
        try:
            for file in os.listdir(output_dir):
                path = os.path.join(output_dir, file)
                if file.startswith("temp_payload_") and os.path.isfile(path):
                    os.remove(path)
                # Removed: cleanup for temp_combined_payload_
        except Exception as e:
            print(f"[Cleanup ERROR] {e}")

    return result


# --- Extraction Function ---
def extract_payload(file_path: str, password: str = None, key_data: bytes = None) -> dict:
    """
    Extracts hidden payload from a carrier file, handling encryption,
    masking, and key file requirements. (Simplified for no deception/matryoshka layers).
    """
    try:
        with open(file_path, "rb") as f:
            content = f.read()

        # Removed: real_start_index, real_end_index, and combined payload logic (FAKE_TAG/REAL_TAG)
        # Directly extract header and payload, as no fake payloads are supported
        header_index = content.find(HEADER_MARKER)
        if header_index == -1:
            return {"status": "error", "message": "Metadata not found in file."}

        start = header_index + len(HEADER_MARKER)
        end = content.find(b"\0", start)
        if end == -1:
            return {"status": "error", "message": "Malformed metadata block."}

        metadata_raw = content[start:end]
        try:
            metadata = json.loads(metadata_raw.decode("utf-8"))
        except json.JSONDecodeError:
            return {"status": "error", "message": "Metadata corrupted."}

        payload_data = content[end + 1:]
        print(f"DEBUG EXTRACT: Payload data extracted: {len(payload_data)} bytes") # Adjusted print statement

        if metadata.get("whitened"):
            payload_data = apply_data_dewhitening(payload_data)
            print(f"DEBUG EXTRACT: Payload data AFTER de-whitening: {len(payload_data)} bytes")

        # --- Handle Decryption and Key File Requirement ---
        encryption_algo = metadata.get("encryption")
        generate_key_used = metadata.get("generate_key_used", False)

        print(f"DEBUG EXTRACT: Encryption algorithm detected: {encryption_algo}")
        print(f"DEBUG EXTRACT: 'Generate Key' used (from metadata): {generate_key_used}")
        print(f"DEBUG EXTRACT: Provided password: {bool(password)}")
        print(f"DEBUG EXTRACT: Provided key_data: {bool(key_data)}")

        # If 'generate_key_used' was true, then key_data is required, regardless of encryption
        if generate_key_used and not key_data:
            return {"status": "error",
                    "message": "A key file was used during embedding. Please provide the key file for extraction."}

        if encryption_algo and encryption_algo != "None":
            if not password:
                return {"status": "error", "message": "Payload is encrypted. A password is required for extraction."}

            try:
                # The decrypt_file function in core/encryption.py should handle the single layer decryption
                payload_data = decrypt_file(payload_data, password, algorithm=encryption_algo, key_data=key_data)
                print(f"DEBUG EXTRACT: Payload data AFTER decryption: {len(payload_data)} bytes")
            except (ValueError, InvalidToken) as e:
                print(f"DEBUG EXTRACT: Decryption failed with exception: {e}")
                return {"status": "error",
                        "message": f"Decryption failed: Incorrect password/key, or corrupted data. ({e})"}
        # --- END Decryption and Key File Requirement ---

        output_dir = get_output_dir()
        os.makedirs(output_dir, exist_ok=True)
        filename = os.path.basename(file_path)
        name, _ = os.path.splitext(filename)

        original_filename = metadata.get("original_filename", f"extracted_{name}.bin")
        out_path = os.path.join(output_dir, original_filename)

        if os.path.exists(out_path):
            base, ext = os.path.splitext(original_filename)
            out_path = os.path.join(output_dir, f"{base}_{uuid.uuid4().hex[:4]}{ext}")

        with open(out_path, "wb") as out:
            out.write(payload_data)

        return {"status": "success", "output_file": out_path, "metadata": metadata}

    except Exception as e:
        print(f"Error during extraction: {e}")
        return {"status": "error", "message": str(e)}