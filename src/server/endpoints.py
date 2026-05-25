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
        return jsonify({"error": "Invalid JSON body"}), 400

    required = ("username", "server_share", "encrypted_vault", "vault_nonce")
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}"}), 400

    username = data["username"]
    server_share = data["server_share"]
    try:
        encrypted_vault = _b64_decode(data["encrypted_vault"])
        vault_nonce = _b64_decode(data["vault_nonce"])
    except (binascii.Error, ValueError):
        return jsonify({"error": "encrypted_vault and vault_nonce must be base64"}), 400

    if not isinstance(username, str) or not username.strip():
        return jsonify({"error": "username must be a non-empty string"}), 400
    if not isinstance(server_share, str) or not server_share:
        return jsonify({"error": "server_share must be a non-empty string"}), 400
    if len(vault_nonce) != 12:
        return jsonify({"error": "vault_nonce must be 12 bytes"}), 400

    conn = get_db()
    try:
        existing = conn.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()
        if existing:
            return jsonify({"error": "User already exists"}), 409

        cursor = conn.execute(
            "INSERT INTO users (username) VALUES (?)", (username,)
        )
        user_id = cursor.lastrowid
        conn.execute(
            "INSERT INTO vaults (user_id, server_share, encrypted_vault, vault_nonce) "
            "VALUES (?, ?, ?, ?)",
            (user_id, server_share, encrypted_vault, vault_nonce),
        )
        conn.commit()
        return jsonify({"status": "created", "username": username}), 201
    finally:
        conn.close()


@vault_bp.route("/vault/<username>", methods=["GET"])
def get_vault(username: str):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT v.server_share, v.encrypted_vault, v.vault_nonce "
            "FROM vaults v JOIN users u ON u.id = v.user_id "
            "WHERE u.username = ?",
            (username,),
        ).fetchone()
        if row is None:
            return jsonify({"error": "User not found"}), 404
        return jsonify({
            "server_share": row["server_share"],
            "encrypted_vault": _b64_encode(row["encrypted_vault"]),
            "vault_nonce": _b64_encode(row["vault_nonce"]),
        }), 200
    finally:
        conn.close()


@vault_bp.route("/vault/<username>", methods=["PUT"])
def update_vault(username: str):
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON body"}), 400

    if "encrypted_vault" not in data or "vault_nonce" not in data:
        return jsonify({"error": "Missing encrypted_vault or vault_nonce"}), 400

    try:
        encrypted_vault = _b64_decode(data["encrypted_vault"])
        vault_nonce = _b64_decode(data["vault_nonce"])
    except (binascii.Error, ValueError):
        return jsonify({"error": "encrypted_vault and vault_nonce must be base64"}), 400

    if len(vault_nonce) != 12:
        return jsonify({"error": "vault_nonce must be 12 bytes"}), 400

    conn = get_db()
    try:
        row = conn.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()
        if row is None:
            return jsonify({"error": "User not found"}), 404

        conn.execute(
            "UPDATE vaults SET encrypted_vault = ?, vault_nonce = ?, "
            "updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
            (encrypted_vault, vault_nonce, row["id"]),
        )
        conn.commit()
        return jsonify({"status": "updated", "username": username}), 200
    finally:
        conn.close()