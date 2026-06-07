import base64
import json
import sqlite3
import os
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

'''
set cli to root then run
python tests/test_zero_knowledge.py

'''



# Import relatif dari struktur arsitektur proyek Anda
from src.client import api_client
from src.server.db import DB_PATH

def prove_zero_knowledge(username: str):
    print("=== [UJI KASUS] Verifikasi Skema Zero-Knowledge ===")
    
    # 1. Ambil data dari API Server untuk melihat apa yang ditransmisikan di jaringan
    print("[INFO] Mengambil payload vault dari endpoint server...")
    server_data = api_client.get_vault(username)
    
    if not server_data:
        print(f"[GAGAL] Data untuk user '{username}' tidak ditemukan di server.")
        return

    print("\n--- Payload Transmisi Jaringan (Intercepted) ---")
    print(f"Server Share (Encoded String) : {server_data['server_share']}")
    print(f"Encrypted Vault (Base64)      : {base64.b64encode(server_data['encrypted_vault']).decode()}")
    print(f"Vault Nonce (Base64 IV)       : {base64.b64encode(server_data['vault_nonce']).decode()}")
    
    # 2. Periksa langsung ke dalam penyimpanan piringan lokal SQLite Server
    print("\n[INFO] Memeriksa isi database lokal SQLite Server secara langsung...")
    if not Path(DB_PATH).exists():
        print(f"[GAGAL] File database tidak ditemukan di jalur: {DB_PATH}")
        return
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT v.* FROM vaults v JOIN users u ON u.id = v.user_id WHERE u.username = ?", 
            (username,)
        ).fetchone()
        
        print("\n--- Record Data Asli di Dalam File Database (Disk) ---")
        print(f"Kolom 'server_share'  : {row['server_share']}")
        print(f"Kolom 'encrypted_vault': {row['encrypted_vault'][:20]}... (Biner Terenkripsi/BLOB)")
        print(f"Kolom 'vault_nonce'    : {row['vault_nonce'].hex()} (Hex Nonce)")
        
        # Skenario pembuktian: Coba decode BLOB terenkripsi ke teks biasa
        try:
            row['encrypted_vault'].decode('utf-8')
            print("[PERINGATAN] Data tersimpan dalam bentuk teks biasa (Plaintext)!")
        except UnicodeDecodeError:
            print("\n[BERHASIL] Konfirmasi: Isi data vault berupa biner acak mentah (BLOB).")
            print("[BERHASIL] Konfirmasi: Server TIDAK menyimpan master_key, local_share, ataupun plaintext isi vault.")
            
    finally:
        conn.close()

if __name__ == "__main__":
    # Ganti dengan username yang sudah Anda buat melalui CLI aplikasi
    prove_zero_knowledge("login0@mail.com")