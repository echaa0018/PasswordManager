# Distributed Password Manager (Shamir SSS)

A distributed password manager that protects each user's vault with a master key
split via **Shamir's Secret Sharing (2-of-3)**. One share lives on the client,
one on the server, and one is handed to the user as a recovery code. Any two
shares reconstruct the key which means the vault survives both server outages and
local-disk loss while no single location ever holds enough to decrypt it.

The server is **zero-knowledge**. It stores only the encrypted vault blob,
its nonce, and the opaque server share. It never sees the master password,
master key, plaintext entries, or the recovery share.

## Contributors

| NIM | Name |
|-------|-----------|
| 18223068 | Muhammad Arya Prihastono Prihastono |
| 18223082 | Mahesa Satria Prayata |
| 10123065 | Raja Muhammad Arkan H M A |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11+ |
| KDF | Argon2id (`argon2-cffi`) |
| Symmetric crypto | AES-128-GCM (`cryptography`) |
| Secret sharing | Shamir over GF(2^8) (`pycryptodome`) |
| Password generation | `secrets` (CSPRNG over `os.urandom`) |
| Server | Flask + SQLite |
| Client UI | Rich (terminal) |
| Bonus (Visual Crypto) | qrcode, Pillow, NumPy, OpenCV |

## Dependencies

Listed in `requirements.txt`:

```
cryptography
pycryptodome
argon2-cffi
flask
requests
rich
pytest
qrcode[pil]
opencv-python
pillow
numpy
pyperclip
```

## How to Run

**Environment:** Python 3.11+ recommended. Server and client communicate over
`http://127.0.0.1:5000` only (local loopback).

Run all commands from the project root.

```bash
pip install -r requirements.txt

# Terminal 1 — start the vault server
python scripts/run_server.py

# Terminal 2 — start the client
python scripts/run_client.py
```

## File Structure

```
.
├── src/                          # All application source code
│   ├── client/                   #   Client-side logic
│   │   ├── api_client.py         #     HTTP wrapper for the vault server
│   │   ├── flows/                #     Create-vault / login / CRUD pipelines
│   │   │   ├── create_vault.py
│   │   │   ├── login_normal.py
│   │   │   ├── login_backup.py
│   │   │   └── vault_ops.py
│   │   ├── main.py               #     CLI entry point
│   │   ├── state.py              #     Session state machine (LOCKED/NORMAL/BACKUP)
│   │   ├── ui/                   #     Rich-based menus and prompts
│   │   │   ├── menu.py
│   │   │   └── prompts.py
│   │   └── vault.py              #     Vault + PasswordEntry models
│   ├── crypto/                   #   Crypto primitives (audited as a unit)
│   │   ├── aes_gcm.py            #     AES-128-GCM authenticated encryption
│   │   ├── csprng.py             #     CSPRNG password generator
│   │   ├── kdf.py                #     Argon2id key derivation
│   │   ├── shamir.py             #     Shamir (2,3) secret sharing
│   │   └── share_format.py       #     Share encoding for display/transport
│   ├── server/                   #   Zero-knowledge vault server
│   │   ├── app.py                #     Flask app factory
│   │   ├── db.py                 #     SQLite schema and connection
│   │   └── endpoints.py          #     /vault/* + /health endpoints
│   ├── storage/
│   │   └── local_store.py        #   Encrypted local share + backup vault on disk
│   └── bonus/
│       └── visual_crypto.py      #   (2,2) visual cryptography for QR recovery share
├── scripts/                      # Entry-point launchers
│   ├── run_server.py
│   └── run_client.py
├── tests/                        # Pytest unit tests for crypto primitives
├── docs/                         # Project documentation (laporan)
├── data/                         # Local + server runtime state (gitignored)
│   ├── client/                   #   local_share.enc, backup_vault.enc
│   └── server/                   #   vault.db
├── conftest.py                   # Pytest path config (adds src/ to sys.path)
├── requirements.txt
├── README.md
└── .gitignore
```

## Security Notes

1. **Zero-knowledge server.** `server/` never imports `crypto/` (no key
   derivation, no encryption, no Shamir on the server). The DB schema has only:
   `users(id, username, created_at)` and `vaults(id, user_id, server_share,
   encrypted_vault, vault_nonce, updated_at)`.
2. **Master key never persisted.** The 16-byte master key lives only in the
   in-memory `SessionState`. `SessionState.clear()` wipes it on logout.
3. **Fresh AES-GCM nonce on every encryption.** Each vault re-encryption (on
   create, edit, delete) draws a new 12-byte nonce from `secrets.token_bytes`.
4. **Recovery share displayed once.** The create flow prints it to the
   terminal and discards it. It is never written to disk and never sent to the
   server.
5. **Backup mode is strictly read-only.** All mutating CRUD functions check
   `session.is_read_only()` first and refuse if true.