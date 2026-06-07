import sys
from pathlib import Path
import cv2
import numpy as np
from PIL import Image

# Menyelaraskan sys.path agar modul internal proyek dapat diimpor langsung
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT  / "src"))

# Skenario fallback jika struktur folder kustom berbeda
if not (Path("src").exists()):
    sys.path.insert(0, str(_ROOT))

from client.ui.prompts import display_success, display_error, display_info
from bonus.visual_crypto import _to_bin, _to_pil, _QR_DETECTOR


def combine_qr_visual(share1_img: Image.Image, share2_img: Image.Image) -> Image.Image:
    """
    Menggabungkan dua Visual Cryptography Share secara digital menggunakan operasi logika OR
    untuk merekonstruksi citra QR Code asli (Masing-masing piksel sub-pixel ditumpuk).
    """
    arr1 = _to_bin(share1_img)
    arr2 = _to_bin(share2_img)
    
    if arr1.shape != arr2.shape:
        raise ValueError("Ukuran dimensi gambar share1 dan share2 tidak cocok!")
        
    # Operasi Overlapping Kriptografi Visual (2-of-2):
    # Jika salah satu lembar mika berwarna hitam (1), maka hasil tumpukannya menjadi Hitam (1).
    combined_bin = np.bitwise_or(arr1, arr2)
    
    return _to_pil(combined_bin)


def run_standalone_reconstruction(username: str = "login0@mail.com"):
    print("\n" + "="*70)
    display_info(f"[UJI KASUS] Rekonstruksi & Scanner Otomatis Visual Cryptography")
    display_info(f"Target Direktori User: data/client/vc_{username}")
    print("="*70)
    
    user_dir = Path(f"data/client/vc_{username}")
    path_share1 = user_dir / "share1.png"
    path_share2 = user_dir / "share2.png"
    
    if not path_share1.exists() or not path_share2.exists():
        display_error(f"Gagal: Berkas pecahan komponen tidak lengkap di folder target!")
        print(f"  -> Pastikan '{path_share1.name}' & '{path_share2.name}' sudah tergenerasi.")
        print("="*70 + "\n")
        return None
        
    print("[1/3] Memuat komponen gambar biner mika acak (noise)...")
    s1 = Image.open(path_share1)
    s2 = Image.open(path_share2)
    
    print("[2/3] Mengeksekusi rekonstruksi digital via matriks bitwise OR...")
    try:
        reconstructed_img = combine_qr_visual(s1, s2)
        
        # Simpan hasil gabungan ke folder lokal user untuk pembuktian uji bab IX
        reconstructed_path = user_dir / "reconstructed_qr.png"
        reconstructed_img.save(reconstructed_path)
        display_success(f"Citra QR hasil penggabungan disalin ke: {reconstructed_path}")
        
        # Opsional: Buka popup gambar jika os mendukung GUI antarmuka
        # reconstructed_img.show(title="Hasil Penggabungan Kriptografi Visual")
        
    except Exception as e:
        display_error(f"Gagal memproses tumpukan gambar: {e}")
        return None
        
    print("[3/3] Mengirimkan gambar rekonstruksi ke OpenCV QRCodeDetector...")
    # Konversi citra objek PIL ke struktur numpy grayscale array untuk OpenCV
    open_cv_image = np.array(reconstructed_img.convert("L"))
    
    # Deteksi dan Decode string di dalam QR Code
    data, bbox, straight_qrcode = _QR_DETECTOR.detectAndDecode(open_cv_image)
    
    if data:
        display_success("Matriks Anchor QR Code VALID dan BERHASIL dipindai oleh sistem!")
        print("\n" + "-" * 50)
        print(f"[NILAI RECOVERY SHARE ASLI]:\n{data}")
        print("-" * 50)
        print("="*70 + "\n")
        return data
    else:
        display_error("Kesalahan Dekoder: Struktur matriks QR terdeteksi namun datanya rusak/unreadable.")
        print("  Tips: Pastikan box_size dan sub-pixel tidak mengalami interpolasi blur saat disimpan.")
        print("="*70 + "\n")
        return None


if __name__ == "__main__":
    # Masukkan nama user target yang ingin diuji penggabungan QR miliknya
    import sys
    target_user = sys.argv[1] if len(sys.argv) > 1 else "login2@mail.com"
    run_standalone_reconstruction(username=target_user)
