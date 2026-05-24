import secrets
import pytest
from cryptography.exceptions import InvalidTag
from crypto.aes_gcm import decrypt, encrypt


def test_roundtrip():
    key = secrets.token_bytes(16)
    plaintext = b"Madoka Magica"
    ciphertext, nonce = encrypt(plaintext, key)
    assert ciphertext != plaintext
    assert len(nonce) == 12
    assert decrypt(ciphertext, key, nonce) == plaintext


def test_empty_plaintext():
    key = secrets.token_bytes(16)
    ciphertext, nonce = encrypt(b"", key)
    assert decrypt(ciphertext, key, nonce) == b""


def test_wrong_key_fails():
    key = secrets.token_bytes(16)
    wrong_key = secrets.token_bytes(16)
    ciphertext, nonce = encrypt(b"secret", key)
    with pytest.raises(InvalidTag):
        decrypt(ciphertext, wrong_key, nonce)


def test_wrong_nonce_fails():
    key = secrets.token_bytes(16)
    ciphertext, _ = encrypt(b"secret", key)
    wrong_nonce = secrets.token_bytes(12)
    with pytest.raises(InvalidTag):
        decrypt(ciphertext, key, wrong_nonce)


def test_tampered_ciphertext_fails():
    key = secrets.token_bytes(16)
    ciphertext, nonce = encrypt(b"secret", key)
    tampered = bytes([ciphertext[0] ^ 0x01]) + ciphertext[1:]
    with pytest.raises(InvalidTag):
        decrypt(tampered, key, nonce)


def test_invalid_key_length_encrypt():
    with pytest.raises(ValueError):
        encrypt(b"data", b"shortkey")


def test_invalid_key_length_decrypt():
    with pytest.raises(ValueError):
        decrypt(b"x" * 32, b"shortkey", b"n" * 12)


def test_nonce_is_fresh_each_call():
    key = secrets.token_bytes(16)
    _, nonce1 = encrypt(b"same", key)
    _, nonce2 = encrypt(b"same", key)
    assert nonce1 != nonce2