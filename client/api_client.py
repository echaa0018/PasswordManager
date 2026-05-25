import base64
import requests

BASE_URL = "http://127.0.0.1:5000"
TIMEOUT = 5


def _b64e(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def _b64d(value: str) -> bytes:
    return base64.b64decode(value.encode("ascii"))


def is_server_available() -> bool:
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
        return r.status_code == 200
    except requests.exceptions.RequestException:
        return False


def create_vault(
    username: str,
    server_share: str,
    encrypted_vault: bytes,
    vault_nonce: bytes,
) -> bool:
    payload = {
        "username": username,
        "server_share": server_share,
        "encrypted_vault": _b64e(encrypted_vault),
        "vault_nonce": _b64e(vault_nonce),
    }
    try:
        r = requests.post(f"{BASE_URL}/vault/create", json=payload, timeout=TIMEOUT)
        return r.status_code == 201
    except requests.exceptions.RequestException:
        return False


def get_vault(username: str) -> dict | None:
    try:
        r = requests.get(f"{BASE_URL}/vault/{username}", timeout=TIMEOUT)
        if r.status_code != 200:
            return None
        data = r.json()
        return {
            "server_share": data["server_share"],
            "encrypted_vault": _b64d(data["encrypted_vault"]),
            "vault_nonce": _b64d(data["vault_nonce"]),
        }
    except (requests.exceptions.RequestException, ValueError, KeyError):
        return None


def update_vault(username: str, encrypted_vault: bytes, vault_nonce: bytes) -> bool:
    payload = {
        "encrypted_vault": _b64e(encrypted_vault),
        "vault_nonce": _b64e(vault_nonce),
    }
    try:
        r = requests.put(f"{BASE_URL}/vault/{username}", json=payload, timeout=TIMEOUT)
        return r.status_code == 200
    except requests.exceptions.RequestException:
        return False