import base64
import json
from pathlib import Path

LOCAL_SHARE_PATH = Path("data/client/local_share.enc")
BACKUP_VAULT_PATH = Path("data/client/backup_vault.enc")

KDF_PARAMS = {"time_cost": 3, "memory_cost": 65536, "parallelism": 2}


def _b64e(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def _b64d(value: str) -> bytes:
    return base64.b64decode(value.encode("ascii"))


def _ensure_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def save_local_share(encrypted_share: bytes, nonce: bytes, kdf_salt: bytes) -> None:
    _ensure_dir(LOCAL_SHARE_PATH)
    payload = {
        "encrypted_share": _b64e(encrypted_share),
        "nonce": _b64e(nonce),
        "kdf_salt": _b64e(kdf_salt),
        "kdf_params": KDF_PARAMS,
    }
    LOCAL_SHARE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_local_share() -> dict | None:
    if not LOCAL_SHARE_PATH.exists():
        return None
    raw = json.loads(LOCAL_SHARE_PATH.read_text(encoding="utf-8"))
    return {
        "encrypted_share": _b64d(raw["encrypted_share"]),
        "nonce": _b64d(raw["nonce"]),
        "kdf_salt": _b64d(raw["kdf_salt"]),
        "kdf_params": raw.get("kdf_params", KDF_PARAMS),
    }


def save_backup_vault(encrypted_vault: bytes, vault_nonce: bytes) -> None:
    _ensure_dir(BACKUP_VAULT_PATH)
    payload = {
        "encrypted_vault": _b64e(encrypted_vault),
        "vault_nonce": _b64e(vault_nonce),
    }
    BACKUP_VAULT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_backup_vault() -> dict | None:
    if not BACKUP_VAULT_PATH.exists():
        return None
    raw = json.loads(BACKUP_VAULT_PATH.read_text(encoding="utf-8"))
    return {
        "encrypted_vault": _b64d(raw["encrypted_vault"]),
        "vault_nonce": _b64d(raw["vault_nonce"]),
    }


def local_share_exists() -> bool:
    return LOCAL_SHARE_PATH.exists()