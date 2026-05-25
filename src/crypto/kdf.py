import secrets
import argon2
from argon2.low_level import Type, hash_secret_raw

KDF_TIME_COST = 3
KDF_MEMORY_COST = 65536  # 64 MB
KDF_PARALLELISM = 2
KDF_HASH_LEN = 16  # 128 bits so it matches AES-128 key size
KDF_SALT_LEN = 16


def derive_key(master_password: str, salt: bytes | None = None) -> tuple[bytes, bytes]:
    if salt is None:
        salt = secrets.token_bytes(KDF_SALT_LEN)
    key = hash_secret_raw(
        secret=master_password.encode("utf-8"),
        salt=salt,
        time_cost=KDF_TIME_COST,
        memory_cost=KDF_MEMORY_COST,
        parallelism=KDF_PARALLELISM,
        hash_len=KDF_HASH_LEN,
        type=Type.ID,
    )
    return key, salt


def derive_key_from_salt(master_password: str, salt: bytes) -> bytes:
    key, _ = derive_key(master_password, salt)
    return key