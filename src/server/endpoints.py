import base64
import binascii
from flask import Blueprint, jsonify, request
from server.db import get_db

vault_bp = Blueprint("vault", __name__)


def _b64_decode(value: str) -> bytes:
    return base64.b64decode(value.encode("ascii"), validate=True)


def _b64_encode(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


@vault_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@vault_bp.route("/vault/create", methods=["POST"])
def create_vault():
    data = request.get_json(silent=True)
    if not data:
        print("[SERVER ERROR] Create Vault failed: Request payload missing or invalid JSON format.")
        return jsonify({"error": "Invalid JSON body"}), 400

    required = ("username", "server_share", "encrypted_vault", "vault_nonce")
    missing = [f for f in required if f not in data]
    if missing:
        print(f"[SERVER ERROR] Create Vault failed: Missing required database fields: {missing}")
        return jsonify({"error": f"Missing fields: {missing}"}), 400

    username = data["username"]
    server_share = data["server_share"]
    
    # Validation of data and nonce encoding formats
    print(f"[SERVER STATUS] Parsing incoming payload metadata for user '{username}'...")
    try:
        encrypted_vault = _b64_decode(data["encrypted_vault"])
        vault_nonce = _b64_decode(data["vault_nonce"])
    except (binascii.Error, ValueError) as e:
        print(f"[SERVER ERROR] Cryptographic extraction failed. Payload data or initialization vector cannot be parsed. ({e})")
        return jsonify({"error": "encrypted_vault and vault_nonce must be valid base64 strings"}), 400

    if not isinstance(username, str) or not username.strip():
        return jsonify({"error": "username must be a non-empty string"}), 400
    if not isinstance(server_share, str) or not server_share:
        return jsonify({"error": "server_share must be a non-empty string"}), 400
    
    # Nonce verification check
    if len(vault_nonce) != 12:
        print(f"[SERVER ERROR] Cryptographic structural error: Vault initialization vector is {len(vault_nonce)} bytes (Expected: 12 bytes).")
        return jsonify({"error": "vault_nonce configuration error: must be exactly 12 bytes"}), 400

    conn = get_db()
    try:
        existing = conn.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()
        if existing:
            print(f"[SERVER ERROR] Resource conflict: Account registration failed because user '{username}' already exists.")
            return jsonify({"error": "User already exists"}), 409

        cursor = conn.execute(
            "INSERT INTO users (username) VALUES (?)", (username,)
        )
        user_id = cursor.lastrowid
        
        print(f"[SERVER STATUS] Persisting initial payload and server share credentials for user ID {user_id}...")
        conn.execute(
            "INSERT INTO vaults (user_id, server_share, encrypted_vault, vault_nonce) "
            "VALUES (?, ?, ?, ?)",
            (user_id, server_share, encrypted_vault, vault_nonce),
        )
        conn.commit()
        print(f"[SERVER SUCCESS] Vault safely initialized and securely stored for user '{username}'.")
        return jsonify({"status": "created", "username": username}), 201
    except Exception as e:
        print(f"[SERVER ERROR] Database commit failure during vault setup: {e}")
        return jsonify({"error": "Internal ledger storage error occurred"}), 500
    finally:
        conn.close()


@vault_bp.route("/vault/<username>", methods=["GET"])
def get_vault(username: str):
    # This route retrieves data required for regular authentication flows.
    # On the client-side, the combination of Server Share and Local Share are decrypted/reconstructed.
    print(f"[SERVER STATUS] Authentication fetch requested. Retrieving remote cryptographic shares for user '{username}'...")
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT v.server_share, v.encrypted_vault, v.vault_nonce "
            "FROM vaults v JOIN users u ON u.id = v.user_id "
            "WHERE u.username = ?",
            (username,),
        ).fetchone()
        
        if row is None:
            print(f"[SERVER ERROR] Authentication fetch failed: Credentials for user '{username}' not found.")
            return jsonify({"error": "User not found"}), 404
            
        print(f"[SERVER SUCCESS] Dispatched server share and vault payload successfully for user '{username}'. Client can now process decryption.")
        return jsonify({
            "server_share": row["server_share"],
            "encrypted_vault": _b64_encode(row["encrypted_vault"]),
            "vault_nonce": _b64_encode(row["vault_nonce"]),
        }), 200
    except Exception as e:
        print(f"[SERVER ERROR] Error fetching authentication credentials: {e}")
        return jsonify({"error": "Failed to retrieve cryptographic share components"}), 500
    finally:
        conn.close()


@vault_bp.route("/vault/<username>", methods=["PUT"])
def update_vault(username: str):
    data = request.get_json(silent=True)
    if not data:
        print(f"[SERVER ERROR] Modification failed for user '{username}': Missing update payload data.")
        return jsonify({"error": "Invalid JSON body"}), 400

    if "encrypted_vault" not in data or "vault_nonce" not in data:
        print(f"[SERVER ERROR] Modification failed for user '{username}': Missing required data fields or cryptographic components.")
        return jsonify({"error": "Missing encrypted_vault or vault_nonce payload components"}), 400

    # Message of Editing Nonce and Data on Server Vault and Local Vault + Errors
    print(f"[SERVER STATUS] Initiating data modify request for user '{username}'...")
    try:
        encrypted_vault = _b64_decode(data["encrypted_vault"])
        vault_nonce = _b64_decode(data["vault_nonce"])
    except (binascii.Error, ValueError) as e:
        print(f"[SERVER ERROR] Modification decoding error for user '{username}': New data or nonce payload strings are corrupted. ({e})")
        return jsonify({"error": "Payload items must be valid base64 strings"}), 400

    # Validate Nonce structure during edit
    if len(vault_nonce) != 12:
        print(f"[SERVER ERROR] Nonce modification rejected for user '{username}': Proposed initialization vector is {len(vault_nonce)} bytes (Expected: 12 bytes).")
        return jsonify({"error": "Vault initialization vector update error: Must match structural constraints (12 bytes)"}), 400

    conn = get_db()
    try:
        row = conn.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()
        if row is None:
            print(f"[SERVER ERROR] Modification rejected: User account for '{username}' does not exist.")
            return jsonify({"error": "User not found"}), 404

        # Track prior signature properties before overwrite
        print(f"[SERVER STATUS] Modifying encrypted data block and initialization parameters for user '{username}'...")
        conn.execute(
            "UPDATE vaults SET encrypted_vault = ?, vault_nonce = ?, "
            "updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
            (encrypted_vault, vault_nonce, row["id"]),
        )
        conn.commit()
        
        print(f"[SERVER SUCCESS] Server vault database updated. New cryptogram and updated nonces saved successfully for user '{username}'.")
        print(f"[SERVER INFO] Client must now proceed to sync and save local backup configurations.")
        return jsonify({"status": "updated", "username": username}), 200
    except Exception as e:
        print(f"[SERVER ERROR] Internal transaction aborted during vault modification for user '{username}': {e}")
        return jsonify({"error": "Failed to rewrite vault records to database ledger"}), 500
    finally:
        conn.close()