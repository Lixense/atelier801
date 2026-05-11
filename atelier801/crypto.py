import hashlib
import base64

FIXED_ARRAY = [-9, 25, -92, -37, -117, 18, 112, -95, -5, -108, 40, -83, -107, 73, -92, -102, 46, -52, 49, -118, -79, -56, -72, 63, -69, -98, -118, -22, 46, -16, -22, -111]


def shakikoo_hash_hex(password):
    """Compute SHA-256 and return as lowercase hex string"""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def crypte(password):
    """Encrypt password using Atelier 801's SHAKikoo algorithm"""
    h = shakikoo_hash_hex(password)

    combined = []
    for b in h:
        combined.append(ord(b))

    for i, val in enumerate(FIXED_ARRAY):
        combined.append(val + i)

    hex_str = ''.join(f'{b & 0xFF:02x}' for b in combined)
    sha256_hash = hashlib.sha256(bytes.fromhex(hex_str)).digest()

    return base64.b64encode(sha256_hash).decode('utf-8')
