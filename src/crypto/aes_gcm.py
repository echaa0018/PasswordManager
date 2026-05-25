import secrets
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

KEY_LEN = 16   # AES-128
NONCE_LEN = 12  # GCM standard


def _validate_key(key: bytes) -> None:
    if len(key) != KEY_LEN:
        raise ValueError(f"Key must be exactly {KEY_LEN} bytes, got {len(key)}")


def encrypt(plaintext: bytes, key: bytes) -> tuple[bytes, bytes]:
    _validate_key(key)
    nonce = secrets.token_bytes(NONCE_LEN)
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, associated_data=None)
    return ciphertext, nonce


def decrypt(ciphertext: bytes, key: bytes, nonce: bytes) -> bytes:
    _validate_key(key)
    return AESGCM(key).decrypt(nonce, ciphertext, associated_data=None)


__all__ = ["encrypt", "decrypt", "InvalidTag"]