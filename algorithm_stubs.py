import os
import numpy as np
from PIL import Image
import pywt
import math
import hashlib
from datetime import datetime
import json
from pydub import AudioSegment
import wave
import contextlib
import tempfile
from scipy.signal import wiener
from scipy.fftpack import dct , idct
from scipy.ndimage import uniform_filter, convolve
from utils.key_encoder import generate_dict_checksum

HEADER_MARKER = b"RYGELHDR\0"

def run_stc(carrier_path, payload_path, output_path):
    """
    STC-like simulation: Embed payload bits into carrier using selective bit flipping with parity-style constraint
    """
    try:
        with open(carrier_path, 'rb') as f:
            carrier_bytes = bytearray(f.read())

        with open(payload_path, 'rb') as f:
            payload = f.read()

        payload_bits = ''.join(f'{byte:08b}' for byte in payload)
        payload_index = 0

        block_size = 8
        max_capacity = len(carrier_bytes) // block_size

        if len(payload_bits) > max_capacity * block_size:
            raise ValueError("Payload too large to embed in carrier.")

        for i in range(0, len(carrier_bytes), block_size):
            if payload_index >= len(payload_bits):
                break

            for j in range(block_size):
                bit_pos = i + j
                if bit_pos >= len(carrier_bytes) or payload_index >= len(payload_bits):
                    break
                target_bit = int(payload_bits[payload_index])
                carrier_bytes[bit_pos] = (carrier_bytes[bit_pos] & 0xFE) | target_bit
                payload_index += 1

        with open(output_path, 'wb') as f:
            f.write(carrier_bytes)

        return output_path

    except Exception as e:
        print(f"[run_stc ERROR] {e}")
        return None


def run_s_uniward(carrier_path, payload_path, output_path):
    """
    Python-based approximation of S-UNIWARD using wavelet-domain distortion modeling.
    Input: grayscale PNG/JPEG, payload file (binary), output file path.
    """
    try:
        img = Image.open(carrier_path).convert("L")
        img_np = np.array(img).astype(np.float32)

        with open(payload_path, 'rb') as f:
            payload = f.read()

        payload_bits = ''.join(f'{b:08b}' for b in payload)
        total_bits = len(payload_bits)

        coeffs = pywt.wavedec2(img_np, 'db8', level=2)
        _, (LH, HL, HH) = coeffs[1]
        cost_map = np.abs(LH) + np.abs(HL) + np.abs(HH)
        cost_map = 1 / (1 + cost_map)
        cost_map = np.clip(cost_map, 0.001, 1.0)

        flat_img = img_np.flatten()
        flat_costs = np.repeat(cost_map.flatten(), 1)
        modifiable_indices = np.argsort(flat_costs)

        if total_bits > len(modifiable_indices):
            raise ValueError("Payload too large to embed with distortion constraints.")

        for i in range(total_bits):
            idx = modifiable_indices[i]
            bit = int(payload_bits[i])
            current_pixel = int(flat_img[idx])
            if (current_pixel % 2) != bit:
                flat_img[idx] = np.clip(current_pixel ^ 1, 0, 255)

        stego_img = Image.fromarray(flat_img.reshape(img_np.shape).astype(np.uint8))
        stego_img.save(output_path)
        return output_path

    except Exception as e:
        print(f"[run_s_uniward ERROR] {e}")
        return None


def run_hugo(carrier_path, payload_path, output_path, gamma=1.0, sigma=1.0):
    """
    HUGO-inspired embedding: calculates pixel-wise costs using directional differences and embeds data minimizing distortion.
    """
    try:
        img = Image.open(carrier_path).convert("L")
        img_np = np.array(img).astype(np.int32)
        padded = np.pad(img_np, pad_width=3, mode='reflect')

        rows, cols = img_np.shape
        costs = np.zeros((rows, cols, 3), dtype=np.float32)  # [decrease, unchanged, increase]

        def eval_cost(k, l, m):
            return (sigma + math.sqrt(k*k + l*l + m*m)) ** -gamma

        def eval_direction(r, c, dr, dc):
            p = [padded[r + dr*k, c + dc*k] for k in range(-3, 4)]
            d = [p[i+1] - p[i] for i in range(6)]
            pixel_costs = np.zeros(3)

            pixel_costs[0] += eval_cost(d[0], d[1], d[2]-1) + eval_cost(d[1], d[2]-1, d[3]+1)
            pixel_costs[2] += eval_cost(d[0], d[1], d[2]+1) + eval_cost(d[1], d[2]+1, d[3]-1)

            pixel_costs[0] += eval_cost(d[2]-1, d[3]+1, d[4]) + eval_cost(d[3]+1, d[4], d[5])
            pixel_costs[2] += eval_cost(d[2]+1, d[3]-1, d[4]) + eval_cost(d[3]-1, d[4], d[5])

            return pixel_costs

        for r in range(rows):
            for c in range(cols):
                r_p, c_p = r + 3, c + 3
                total = eval_direction(r_p, c_p, -1, 1) + eval_direction(r_p, c_p, 0, 1) + \
                        eval_direction(r_p, c_p, 1, 1) + eval_direction(r_p, c_p, 1, 0)
                if img_np[r, c] == 255:
                    total[2] = np.inf
                if img_np[r, c] == 0:
                    total[0] = np.inf
                costs[r, c] = [total[0], 0, total[2]]

        with open(payload_path, 'rb') as f:
            payload = f.read()

        payload_bits = ''.join(f'{b:08b}' for b in payload)
        total_bits = len(payload_bits)

        flat_img = img_np.flatten()
        cost_scores = (costs[:, :, 0] + costs[:, :, 2]).flatten()
        modifiable_indices = np.argsort(cost_scores)

        if total_bits > len(modifiable_indices):
            raise ValueError("Payload too large to embed into carrier.")

        for i in range(total_bits):
            idx = modifiable_indices[i]
            bit = int(payload_bits[i])
            pixel_val = flat_img[idx]
            if (pixel_val % 2) != bit:
                flat_img[idx] = np.clip(pixel_val ^ 1, 0, 255)

        stego_img = Image.fromarray(flat_img.reshape(rows, cols).astype(np.uint8))
        stego_img.save(output_path)
        return output_path

    except Exception as e:
        print(f"[run_hugo ERROR] {e}")
        return None


def run_mvg(carrier_path, payload_path, output_path):
    """
    MVG-like steganography based on local Fisher information embedding simulation.
    """
    try:
        img = Image.open(carrier_path).convert("L")
        img_np = np.array(img).astype(np.float32)
        shape = img_np.shape

        # Read payload and convert to bits
        with open(payload_path, 'rb') as f:
            payload = f.read()
        payload_bits = ''.join(f'{b:08b}' for b in payload)
        total_bits = len(payload_bits)

        # 1. Compute Wiener-filtered residuals
        residuals = img_np - wiener(img_np, (3, 3))

        # 2. Estimate local variance using blockwise DCT energy
        def local_variance(block):
            dct_block = dct(dct(block.T, norm='ortho').T, norm='ortho')
            return np.var(dct_block)

        window_size = 8
        variances = np.zeros(shape)
        for i in range(0, shape[0] - window_size + 1):
            for j in range(0, shape[1] - window_size + 1):
                block = img_np[i:i+window_size, j:j+window_size]
                var = local_variance(block)
                variances[i:i+window_size, j:j+window_size] += var
        variances /= (window_size * window_size)

        # 3. Compute Fisher Information (1/variance^2)
        with np.errstate(divide='ignore'): # handle division by zero
            fisher_map = 1.0 / (variances**2)
            fisher_map = np.nan_to_num(fisher_map, nan=0.0, posinf=0.0, neginf=0.0)
        fisher_flat = fisher_map.flatten()

        # 4. Probabilistic ±1, ±2 pixel modifications
        beta = 2.0
        theta = 0.25
        rand_map = np.random.rand(fisher_flat.shape[0])
        flat_img = img_np.flatten()
        payload_index = 0

        for idx in np.argsort(-fisher_flat): # descending FI importance
            if payload_index >= total_bits:
                break

            bit = int(payload_bits[payload_index])
            current_pixel = flat_img[idx]
            modified_pixel = current_pixel

            # Decide modification based on cost and bit
            cost_plus_1 = fisher_flat[idx]
            cost_minus_1 = fisher_flat[idx]

            if (current_pixel % 2) != bit:
                if rand_map[idx] < (cost_plus_1 / (cost_plus_1 + cost_minus_1)):
                    modified_pixel += 1
                else:
                    modified_pixel -= 1
            else:
                if rand_map[idx] < theta:
                    if rand_map[idx] < (theta * cost_plus_1 / (cost_plus_1 + cost_minus_1)):
                        modified_pixel += 2
                    else:
                        modified_pixel -= 2

            flat_img[idx] = np.clip(modified_pixel, 0, 255)
            payload_index += 1

        stego_img = Image.fromarray(flat_img.reshape(shape).astype(np.uint8))
        stego_img.save(output_path)
        return output_path

    except Exception as e:
        print(f"[run_mvg ERROR] {e}")
        return None


def run_simple_jpg_steg(carrier_path, payload_path=None, output_path=None, extract=False, payload=None):
    """
    Simple JPG/PNG steganography: embeds data by appending it.
    For extraction, it returns the full content to steg_engine.py to parse the header.
    """
    if extract:
        # For extraction, simply read the entire stego file content and return it.
        # steg_engine.py will then be responsible for finding the HEADER_MARKER and parsing.
        try:
            with open(carrier_path, 'rb') as f:
                return f.read()
        except FileNotFoundError:
            print(f"[run_simple_jpg_steg ERROR] Stego file not found at {carrier_path}")
            return b"" # Return empty bytes to indicate failure
        except Exception as e:
            print(f"[run_simple_jpg_steg ERROR] Failed to read stego file for extraction: {e}")
            return b""
    else:
        # --- EMBEDDING LOGIC ---
        try:
            # Read the carrier image
            with open(carrier_path, 'rb') as f:
                carrier_data = f.read()

            # Read the payload data (which includes the header/metadata from steg_engine)
            if payload is None and payload_path:
                with open(payload_path, 'rb') as f:
                    payload = f.read()
            elif payload is None:
                raise ValueError("Payload or payload_path must be provided for embedding.")

            # Simple appending: concatenate carrier data with payload
            # This is a basic method; more robust methods embed within specific data sections
            stego_data = carrier_data + payload

            if output_path is None:
                # Default output path if not provided
                name, ext = os.path.splitext(carrier_path)
                output_path = f"{name}_stego{ext}"

            # Write the new stego file
            with open(output_path, 'wb') as f:
                f.write(stego_data)

            # Clean up temporary payload file if it was created
            if payload_path and payload_path.endswith(".payload"):
                os.remove(payload_path)

            return output_path # Return the path to the created stego file
        except Exception as e:
            print(f"[run_simple_jpg_steg ERROR] during embedding: {e}")
            return None


def mp3_steg(carrier_path, payload_path=None, output_path=None, extract=False, metadata=None):
    """
    MP3 steganography: embeds data into a new ID3v2 tag or appends it.
    For extraction, it returns the full content to steg_engine.py to parse the header.
    """
    if extract:
        # For extraction, simply read the entire stego MP3 file content and return it.
        # steg_engine.py will then be responsible for finding the HEADER_MARKER and parsing.
        try:
            with open(carrier_path, 'rb') as f:
                return f.read()
        except FileNotFoundError:
            print(f"[mp3_steg ERROR] Stego MP3 file not found at {carrier_path}")
            return b""
        except Exception as e:
            print(f"[mp3_steg ERROR] Failed to read stego MP3 file for extraction: {e}")
            return b""
    else:
        # --- EMBEDDING LOGIC ---
        try:
            audio = AudioSegment.from_file(carrier_path)

            if payload is None and payload_path:
                with open(payload_path, 'rb') as f:
                    payload_data = f.read()
            elif payload is None:
                raise ValueError("Payload or payload_path must be provided for embedding.")
            else:
                payload_data = payload

            metadata = metadata or {}
            metadata.setdefault("version", "RYG-1.0")
            metadata.setdefault("timestamp", datetime.now().isoformat())
            metadata.setdefault("type", "genuine")
            metadata.setdefault("dict_checksum", generate_dict_checksum())
            metadata.setdefault("matryoshka_layers", 1)
            metadata.setdefault("encryption", "None")
            metadata.setdefault("masked", False)

            metadata_block = HEADER_MARKER + json.dumps(metadata).encode("utf-8") + b"\0"
            full_payload_with_header = metadata_block + payload_data + b"\0"

            # Append the full payload to the audio data
            # This is a simplified approach; more robust methods might embed in specific ID3 frames
            stego_audio_bytes = audio.export(format="mp3").read() + full_payload_with_header

            if output_path is None:
                name, ext = os.path.splitext(carrier_path)
                output_path = f"{name}_stego{ext}"

            with open(output_path, "wb") as f:
                f.write(stego_audio_bytes)

            if payload_path and payload_path.endswith(".payload"):
                os.remove(payload_path)

            return output_path
        except Exception as e:
            print(f"[mp3_steg ERROR] during embedding: {e}")
            return None


def mp4_steg(carrier_path, payload_path=None, output_path=None, metadata=None, extract=False, payload=None):
    """
    MP4 steganography: embeds data into a 'free' box.
    For extraction, it returns the full content to steg_engine.py to parse the header.
    """
    if extract:
        # For extraction, simply read the entire stego MP4 file content and return it.
        # steg_engine.py will then be responsible for finding the HEADER_MARKER and parsing.
        try:
            with open(carrier_path, 'rb') as f:
                return f.read()
        except FileNotFoundError:
            print(f"[mp4_steg ERROR] Stego MP4 file not found at {carrier_path}")
            return b""
        except Exception as e:
            print(f"[mp4_steg ERROR] Failed to read stego MP4 file for extraction: {e}")
            return b""
    else:
        # --- EMBEDDING LOGIC ---
        try:
            with open(carrier_path, 'rb') as f:
                mp4_data = f.read()

            if payload is None and payload_path:
                with open(payload_path, 'rb') as f:
                    payload_data = f.read()
            elif payload is None:
                raise ValueError("Payload or payload_path must be provided for embedding.")
            else:
                payload_data = payload

            metadata = metadata or {}
            metadata.setdefault("version", "RYG-1.0")
            metadata.setdefault("timestamp", datetime.now().isoformat())
            metadata.setdefault("type", "genuine")
            metadata.setdefault("dict_checksum", generate_dict_checksum())
            metadata.setdefault("matryoshka_layers", 1)
            metadata.setdefault("encryption", "None")
            metadata.setdefault("masked", False)
            metadata_block = HEADER_MARKER + json.dumps(metadata).encode("utf-8") + b"\0"
            full_payload = metadata_block + payload_data + b"\0"

            box_type = b'free'
            payload_box_size = 8 + len(full_payload)
            payload_box = payload_box_size.to_bytes(4, byteorder='big') + box_type + full_payload

            # Insert the 'free' box just before the 'mdat' atom or at the end
            # This is a simplified insertion. A more robust parser would be needed for complex MP4 structures.
            # For simplicity, appending for now.
            new_data = mp4_data + payload_box

            if output_path is None:
                name, ext = os.path.splitext(carrier_path)
                output_path = f"{name}_stego{ext}"

            with open(output_path, "wb") as f:
                f.write(new_data)

            if payload_path and payload_path.endswith(".payload"):
                os.remove(payload_path)

            return output_path

        except Exception as e:
            print(f"[mp4_steg ERROR] during embedding: {e}")
            return None


def run_mipod(carrier_path, payload_path, output_path):
    """
    MIPOD-like simulation: embeds data by modifying DCT coefficients in JPEG/image files.
    """
    try:
        img = Image.open(carrier_path).convert("L")
        img_np = np.array(img, dtype=np.float32)

        # Apply DCT
        dct_coeffs = dct(dct(img_np.T, norm='ortho').T, norm='ortho')

        with open(payload_path, 'rb') as f:
            payload = f.read()

        payload_bits = ''.join(f'{b:08b}' for b in payload)
        total_bits = len(payload_bits)
        payload_idx = 0

        # Simple embedding: embed in low-frequency DCT coefficients
        # This is a highly simplified approach for demonstration
        flat_coeffs = dct_coeffs.flatten()

        if total_bits > len(flat_coeffs) // 2: # Can embed about half the coefficients
            raise ValueError("Payload too large for MIPOD embedding capacity.")

        for i in range(total_bits):
            if payload_idx >= len(flat_coeffs):
                break # No more space

            # Modify coefficient based on payload bit (LSB-like for DCT)
            # This is a conceptual modification, real MIPOD is more complex
            current_coeff = flat_coeffs[payload_idx]
            bit = int(payload_bits[i])

            # Simple LSB-like embedding on the integer part of the coefficient
            int_coeff = int(current_coeff)
            if (int_coeff % 2) != bit:
                if current_coeff >= 0:
                    flat_coeffs[payload_idx] = math.floor(current_coeff) + (1 if bit == 1 else 0) if (math.floor(current_coeff) % 2) != bit else current_coeff
                else:
                    flat_coeffs[payload_idx] = math.ceil(current_coeff) + (1 if bit == 1 else 0) if (math.ceil(current_coeff) % 2) != bit else current_coeff


            flat_coeffs[payload_idx] = (flat_coeffs[payload_idx] & 0xFE) | bit # Simple bit manipulation, conceptual for DCT
            payload_idx += 1


        # Inverse DCT
        modified_dct_coeffs = flat_coeffs.reshape(dct_coeffs.shape)
        stego_img_np = idct(idct(modified_dct_coeffs.T, norm='ortho').T, norm='ortho')

        # Clip and convert back to image
        stego_img_np = np.clip(stego_img_np, 0, 255).astype(np.uint8)
        stego_img = Image.fromarray(stego_img_np)
        stego_img.save(output_path)
        return output_path

    except Exception as e:
        print(f"[run_mipod ERROR] {e}")
        return None


def run_wow(carrier_path, payload_path, output_path):
    """
    WOW-like simulation: Embeds data by modifying pixel values in a way that minimizes changes based on local complexity.
    This is a simplified example.
    """
    try:
        img = Image.open(carrier_path).convert("L")
        img_np = np.array(img).astype(np.float32)

        with open(payload_path, 'rb') as f:
            payload = f.read()
        payload_bits = ''.join(f'{b:08b}' for b in payload)
        total_bits = len(payload_bits)

        # Calculate local complexity (e.g., using variance or gradient magnitude)
        # This is a very simple approximation; actual WOW uses more sophisticated cost functions
        complexity_map = uniform_filter(img_np, size=3) # Example: blur for smoothness, inverse for complexity
        complexity_map = np.abs(img_np - complexity_map) + 1 # Higher difference = higher complexity
        cost_map = 1 / complexity_map # Lower cost for higher complexity areas
        cost_map = np.clip(cost_map, 0.001, 1.0) # Avoid division by zero, ensure valid range

        flat_img = img_np.flatten()
        flat_costs = cost_map.flatten()
        modifiable_indices = np.argsort(flat_costs) # Sort by increasing cost (embed in cheapest first)

        if total_bits > len(modifiable_indices):
            raise ValueError("Payload too large to embed with WOW distortion constraints.")

        for i in range(total_bits):
            idx = modifiable_indices[i]
            bit = int(payload_bits[i])
            current_pixel = int(flat_img[idx])

            if (current_pixel % 2) != bit:
                # Modify pixel to match bit, with minimal change (+1 or -1)
                if current_pixel == 0: # Can only increase
                    flat_img[idx] = 1 if bit == 1 else 0 # Should ideally be 0 if bit is 0
                elif current_pixel == 255: # Can only decrease
                    flat_img[idx] = 254 if bit == 0 else 255 # Should ideally be 255 if bit is 1
                else:
                    # Choose direction that results in lower distortion if possible, or just flip
                    flat_img[idx] = current_pixel ^ 1 # Simple flip for demonstration

        stego_img = Image.fromarray(flat_img.reshape(img_np.shape).astype(np.uint8))
        stego_img.save(output_path)
        return output_path

    except Exception as e:
        print(f"[run_wow ERROR] {e}")
        return None


def synch_steg(carrier_path, payload_path, output_path):
    """
    SYNCH steganography simulation for video (MP4, MKV, AVI).
    Embeds data by appending it to a 'free' box, similar to MP4 handling.
    This is a placeholder for actual video steganography.
    """
    try:
        with open(carrier_path, 'rb') as f:
            video_data = f.read()

        with open(payload_path, 'rb') as f:
            payload_data = f.read()

        # Simple appending of the payload
        stego_data = video_data + payload_data + b"\0" # Add a null terminator for safety

        if output_path is None:
            name, ext = os.path.splitext(carrier_path)
            output_path = f"{name}_stego{ext}"

        with open(output_path, "wb") as f:
            f.write(stego_data)

        if payload_path and payload_path.endswith(".payload"):
            os.remove(payload_path)

        return output_path
    except Exception as e:
        print(f"[synch_steg ERROR] {e}")
        return None