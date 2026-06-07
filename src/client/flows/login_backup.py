from client.state import AppState, SessionState
from client.vault import Vault
from crypto import aes_gcm, kdf, shamir
from crypto.share_format import decode_share
from storage import local_store
from client.ui.prompts import console, display_error, display_success


def run_backup_login(
    username: str,
    master_password: str,
    recovery_share_str: str,
) -> SessionState | None:
    # PERBAIKAN: Muat data berdasarkan identitas user
    local_data = local_store.load_local_share(username)
    if local_data is None:
        display_error(f"Backup Login Failed: Data local share untuk '{username}' tidak ditemukan.")
        return None

    kdf_key = kdf.derive_key_from_salt(master_password, local_data["kdf_salt"])

    console.print("[dim]Decrypting local share...[/dim]")
    try:
        local_share_bytes = aes_gcm.decrypt(
            local_data["encrypted_share"], kdf_key, local_data["nonce"]
        )
    except Exception as e:
        display_error(f"Backup Login Failed: Password salah. ({e})")
        return None

    try:
        local_share = decode_share(local_share_bytes.decode("utf-8"))
        display_success("Local share decrypted successfully.")
    except (ValueError, UnicodeDecodeError):
        return None

    try:
        recovery_share = decode_share(recovery_share_str.strip())
    except ValueError:
        display_error("Format string recovery share tidak valid.")
        return None

    console.print("[dim]Combining shares via Shamir Secret Sharing...[/dim]")
    try:
        master_key = shamir.combine_shares([local_share, recovery_share])
    except Exception as e:
        display_error(f"Backup Login Failed: Rekonstruksi gagal. Kunci share tidak berpasangan. ({e})")
        return None

    # PERBAIKAN: Muat vault terenkripsi spesifik milik akun user tersebut
    backup_data = local_store.load_backup_vault(username)
    if backup_data is None:
        display_error(f"Backup Login Failed: File backup vault untuk '{username}' tidak ditemukan.")
        return None

    try:
        vault_bytes = aes_gcm.decrypt(
            backup_data["encrypted_vault"], master_key, backup_data["vault_nonce"]
        )
    except Exception as e:
        display_error(f"Backup Login Failed: Gagal mendekripsi file cadangan vault menggunakan master key hasil gabungan SSS. ({e})")
        return None

    try:
        vault = Vault.from_bytes(vault_bytes)
    except Exception as e:
        display_error(f"Backup Login Failed: Parsing kegagalan biner database. ({e})")
        return None

    display_success(f"Successfully authenticated as {username} (Read-Only Backup Mode).")
    return SessionState(
        state=AppState.BACKUP,
        username=username,
        master_key=master_key,
        vault=vault,
    )