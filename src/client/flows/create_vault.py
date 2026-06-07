import secrets
from client import api_client
from client.vault import Vault
from crypto import aes_gcm, kdf, shamir
from crypto.share_format import encode_share
from storage import local_store
from client.ui.prompts import console, display_error, display_success

# Import flow enkripsi gambar dari bonus pack
from bonus.visual_crypto import run_visual_crypto_flow

LOCAL_SHARE_INDEX = 0
SERVER_SHARE_INDEX = 1
RECOVERY_SHARE_INDEX = 2


def run_create_vault_flow(
    username: str,
    master_password: str,
) -> tuple[bool, str | None]:
    if not username or not username.strip():
        return False, None
    if not master_password:
        return False, None

    if not api_client.is_server_available():
        return False, None

    master_key = secrets.token_bytes(16)

    empty_vault = Vault()
    vault_bytes = empty_vault.to_bytes()
    encrypted_vault, vault_nonce = aes_gcm.encrypt(vault_bytes, master_key)

    shares = shamir.split_secret(master_key, threshold=2, shares=3)
    local_share = shares[LOCAL_SHARE_INDEX]
    server_share = shares[SERVER_SHARE_INDEX]
    recovery_share = shares[RECOVERY_SHARE_INDEX]

    kdf_key, kdf_salt = kdf.derive_key(master_password)

    console.print("[dim]Encrypting local share...[/dim]")
    try:
        local_share_encoded = encode_share(local_share[0], local_share[1])
        encrypted_local_share, local_nonce = aes_gcm.encrypt(
            local_share_encoded.encode("utf-8"), kdf_key
        )
        display_success("Local share encrypted successfully.")
    except Exception as e:
        display_error(f"Local share encryption failed: {e}")
        return False, None

    server_share_encoded = encode_share(server_share[0], server_share[1])
    recovery_share_encoded = encode_share(recovery_share[0], recovery_share[1])

    created = api_client.create_vault(
        username=username,
        server_share=server_share_encoded,
        encrypted_vault=encrypted_vault,
        vault_nonce=vault_nonce,
    )

    if not created:
        return False, None

    local_store.save_local_share(username, encrypted_local_share, local_nonce, kdf_salt)
    local_store.save_backup_vault(username, encrypted_vault, vault_nonce)

    return True, recovery_share_encoded