import base64
import json
from pathlib import Path

LOCAL_SHARE_FILE = "local_share.enc"
BACKUP_VAULT_FILE = "backup_vault.enc"

KDF_PARAMS = {"time_cost": 3, "memory_cost": 65536, "parallelism": 2}


def _b64e(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def _b64d(value: str) -> bytes:
    return base64.b64decode(value.encode("ascii"))


def _get_user_dir(username: str) -> Path:
    """Mendapatkan direktori khusus per user untuk menghindari overwrite"""
    path = Path(f"data/client/vc_{username}")
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_local_share(username: str, encrypted_share: bytes, nonce: bytes, kdf_salt: bytes) -> None:
    user_dir = _get_user_dir(username)
    # Menggunakan variabel konstanta LOCAL_SHARE_FILE
    file_path = user_dir / LOCAL_SHARE_FILE  
    
    payload = {
        "encrypted_share": _b64e(encrypted_share),
        "nonce": _b64e(nonce),
        "kdf_salt": _b64e(kdf_salt),
        "kdf_params": KDF_PARAMS,
    }
    file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_local_share(username: str) -> dict | None:
    user_dir = _get_user_dir(username)
    # Menggunakan variabel konstanta LOCAL_SHARE_FILE
    file_path = user_dir / LOCAL_SHARE_FILE
    
    if not file_path.exists():
        return None
        
    raw = json.loads(file_path.read_text(encoding="utf-8"))
    return {
        "encrypted_share": _b64d(raw["encrypted_share"]),
        "nonce": _b64d(raw["nonce"]),
        "kdf_salt": _b64d(raw["kdf_salt"]),
        "kdf_params": raw.get("kdf_params", KDF_PARAMS),
    }


def save_backup_vault(username: str, encrypted_vault: bytes, vault_nonce: bytes) -> None:
    user_dir = _get_user_dir(username)
    # Menggunakan variabel konstanta BACKUP_VAULT_FILE
    file_path = user_dir / BACKUP_VAULT_FILE
    
    payload = {
        "encrypted_vault": _b64e(encrypted_vault),
        "vault_nonce": _b64e(vault_nonce),
    }
    file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_backup_vault(username: str) -> dict | None:
    user_dir = _get_user_dir(username)
    # Menggunakan variabel konstanta BACKUP_VAULT_FILE
    file_path = user_dir / BACKUP_VAULT_FILE
    
    if not file_path.exists():
        return None
        
    raw = json.loads(file_path.read_text(encoding="utf-8"))
    return {
        "encrypted_vault": _b64d(raw["encrypted_vault"]),
        "vault_nonce": _b64d(raw["vault_nonce"]),
    }


def local_share_exists(username: str) -> bool:
    user_dir = _get_user_dir(username)
    # Menggunakan variabel konstanta LOCAL_SHARE_FILE untuk pengecekan keberadaan berkas
    return (user_dir / LOCAL_SHARE_FILE).exists()