from client import api_client
from client.state import AppState, SessionState
from client.vault import Vault
from crypto import aes_gcm, kdf, shamir
from crypto.share_format import decode_share
from storage import local_store
from client.ui.prompts import console, display_error, display_success


def run_normal_login(username: str, master_password: str) -> SessionState | None:
    # PERBAIKAN: Berikan argumen username saat memuat data share lokal
    local_data = local_store.load_local_share(username)
    if local_data is None:
        display_error(f"Login Failed: Local share untuk user '{username}' tidak ditemukan di perangkat ini.")
        return None

    kdf_key = kdf.derive_key_from_salt(master_password, local_data["kdf_salt"])

    console.print("[dim]Decrypting local share...[/dim]")
    try:
        local_share_bytes = aes_gcm.decrypt(
            local_data["encrypted_share"], kdf_key, local_data["nonce"]
        )
    except Exception as e:
        display_error(f"Login Failed: Password salah atau integritas data rusak. ({e})")
        return None

    try:
        local_share = decode_share(local_share_bytes.decode("utf-8"))
        display_success("Local share decrypted and decoded successfully.")
    except (ValueError, UnicodeDecodeError):
        return None

    if not api_client.is_server_available():
        return None

    server_data = api_client.get_vault(username)
    if server_data is None:
        return None

    try:
        server_share = decode_share(server_data["server_share"])
    except ValueError as e:
        display_error(f"Login Failed: Format kunci share dari server rusak. ({e})")
        return None

    console.print("[dim]Reconstructing vault master key from shares...[/dim]")
    try:
        master_key = shamir.combine_shares([local_share, server_share])
    except Exception as e:
        display_error(f"Login Failed: Gagal menggabungkan share. Kunci tidak cocok. ({e})")
        return None

    try:
        vault_bytes = aes_gcm.decrypt(
            server_data["encrypted_vault"], master_key, server_data["vault_nonce"]
        )
    except Exception as e:
        display_error(f"Login Failed: Gagal mendekripsi payload vault. ({e})")
        return None

    try:
        vault = Vault.from_bytes(vault_bytes)
    except Exception as e:
        display_error(f"Login Failed: Gagal melakukan parsing objek database vault. ({e})")
        return None

    display_success(f"Successfully authenticated as {username} (Normal Mode).")
    return SessionState(
        state=AppState.NORMAL,
        username=username,
        master_key=master_key,
        vault=vault,
    )