from client.state import AppState, SessionState
from client.vault import Vault
from crypto import aes_gcm, kdf, shamir
from crypto.share_format import decode_share
from storage import local_store


def run_backup_login(
    username: str,
    master_password: str,
    recovery_share_str: str,
) -> SessionState | None:
    local_data = local_store.load_local_share()
    if local_data is None:
        return None

    kdf_key = kdf.derive_key_from_salt(master_password, local_data["kdf_salt"])

    try:
        local_share_bytes = aes_gcm.decrypt(
            local_data["encrypted_share"], kdf_key, local_data["nonce"]
        )
    except Exception:
        return None

    try:
        local_share = decode_share(local_share_bytes.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return None

    try:
        recovery_share = decode_share(recovery_share_str.strip())
    except ValueError:
        return None

    try:
        master_key = shamir.combine_shares([local_share, recovery_share])
    except Exception:
        return None

    backup_data = local_store.load_backup_vault()
    if backup_data is None:
        return None

    try:
        vault_bytes = aes_gcm.decrypt(
            backup_data["encrypted_vault"], master_key, backup_data["vault_nonce"]
        )
    except Exception:
        return None

    try:
        vault = Vault.from_bytes(vault_bytes)
    except Exception:
        return None

    return SessionState(
        state=AppState.BACKUP,
        username=username,
        master_key=master_key,
        vault=vault,
    )
