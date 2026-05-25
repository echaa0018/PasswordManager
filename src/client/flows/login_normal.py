from client import api_client
from client.state import AppState, SessionState
from client.vault import Vault
from crypto import aes_gcm, kdf, shamir
from crypto.share_format import decode_share
from storage import local_store


def run_normal_login(username: str, master_password: str) -> SessionState | None:
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

    if not api_client.is_server_available():
        return None

    server_data = api_client.get_vault(username)
    if server_data is None:
        return None

    try:
        server_share = decode_share(server_data["server_share"])
    except ValueError:
        return None

    try:
        master_key = shamir.combine_shares([local_share, server_share])
    except Exception:
        return None

    try:
        vault_bytes = aes_gcm.decrypt(
            server_data["encrypted_vault"], master_key, server_data["vault_nonce"]
        )
    except Exception:
        return None

    try:
        vault = Vault.from_bytes(vault_bytes)
    except Exception:
        return None

    return SessionState(
        state=AppState.NORMAL,
        username=username,
        master_key=master_key,
        vault=vault,
    )