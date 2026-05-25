from client import api_client
from client.state import SessionState
from client.vault import PasswordEntry
from crypto import aes_gcm
from storage import local_store


def _persist(session: SessionState) -> bool:
    vault_bytes = session.vault.to_bytes()
    encrypted_vault, vault_nonce = aes_gcm.encrypt(vault_bytes, session.master_key)

    if not api_client.update_vault(session.username, encrypted_vault, vault_nonce):
        return False

    local_store.save_backup_vault(encrypted_vault, vault_nonce)
    return True


def add_password(
    session: SessionState,
    service: str,
    username: str,
    password: str,
    notes: str = "",
) -> bool:
    if session.is_read_only() or session.vault is None or session.master_key is None:
        return False

    entry = PasswordEntry.new(service=service, username=username, password=password, notes=notes)
    session.vault.add_entry(entry)

    if not _persist(session):
        session.vault.delete_entry(entry.id)
        return False
    return True


def edit_password(session: SessionState, entry_id: str, **kwargs) -> bool:
    if session.is_read_only() or session.vault is None or session.master_key is None:
        return False

    original = session.vault.get_entry(entry_id)
    if original is None:
        return False

    snapshot = {
        "service": original.service,
        "username": original.username,
        "password": original.password,
        "notes": original.notes,
    }

    if not session.vault.update_entry(entry_id, **kwargs):
        return False

    if not _persist(session):
        session.vault.update_entry(entry_id, **snapshot)
        return False
    return True


def delete_password(session: SessionState, entry_id: str) -> bool:
    if session.is_read_only() or session.vault is None or session.master_key is None:
        return False

    original = session.vault.get_entry(entry_id)
    if original is None:
        return False

    if not session.vault.delete_entry(entry_id):
        return False

    if not _persist(session):
        session.vault.add_entry(original)
        return False
    return True