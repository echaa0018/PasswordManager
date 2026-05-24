import pytest
from crypto.kdf import KDF_HASH_LEN, KDF_SALT_LEN, derive_key, derive_key_from_salt


def test_key_length_is_16_bytes():
    key, salt = derive_key("password")
    assert len(key) == KDF_HASH_LEN == 16
    assert len(salt) == KDF_SALT_LEN == 16


def test_same_password_and_salt_same_key():
    key1, salt = derive_key("password")
    key2 = derive_key_from_salt("password", salt)
    assert key1 == key2


def test_different_password_different_key():
    _, salt = derive_key("password")
    k1 = derive_key_from_salt("password", salt)
    k2 = derive_key_from_salt("Password", salt)
    assert k1 != k2


def test_different_salt_different_key():
    k1, _ = derive_key("password")
    k2, _ = derive_key("password")
    assert k1 != k2, "Fresh salts should produce different keys"


def test_unicode_password():
    pw = "p4ssw0rd-ñ-日本語"
    key, salt = derive_key(pw)
    assert derive_key_from_salt(pw, salt) == key