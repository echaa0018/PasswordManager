from pathlib import Path
import cv2
import numpy as np
import qrcode
from PIL import Image
from client.ui.prompts import display_success, display_error, display_info, confirm_action

_QR_DETECTOR = cv2.QRCodeDetector()


def recovery_share_to_qr(share_str: str, box_size: int = 10, border: int = 4) -> Image.Image:
    """Membuat objek gambar QR Code utuh dari string recovery share"""
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=box_size,
        border=border,
    )
    qr.add_data(share_str)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white").convert("1")


def _to_bin(img: Image.Image) -> np.ndarray:
    arr = np.array(img.convert("L"), dtype=np.uint8)
    return (arr < 128).astype(np.uint8)


def _to_pil(bin_arr: np.ndarray) -> Image.Image:
    return Image.fromarray(np.where(bin_arr == 1, 0, 255).astype(np.uint8), mode="L")


def split_qr_visual(qr_image: Image.Image) -> tuple[Image.Image, Image.Image]:
    """Memecah citra QR utama menjadi 2 Visual Cryptography Share menggunakan vektorisasi cepat"""
    src = _to_bin(qr_image)
    h, w = src.shape
    rng = np.random.default_rng()

    pick = rng.integers(0, 2, size=(h, w), dtype=np.uint8)
    pattern_a = np.stack([pick, 1 - pick], axis=-1)
    pattern_b = np.where(src[..., None] == 1, 1 - pattern_a, pattern_a)

    share1 = pattern_a.reshape(h, w * 2)
    share2 = pattern_b.reshape(h, w * 2)
    return _to_pil(share1), _to_pil(share2)


def combine_qr_visual(share1_img: Image.Image, share2_img: Image.Image) -> Image.Image:
    """
    [DISAMAKAN] Menggabungkan dua Visual Cryptography Share secara digital (Operasi OR biner).
    Nama disamakan dari 'combine_qr_shares' agar tidak merusak dependensi file luar.
    """
    a = _to_bin(share1_img)
    b = _to_bin(share2_img)
    if a.shape != b.shape:
        raise ValueError("Ukuran dimensi kedua gambar share tidak cocok!")
    return _to_pil(np.bitwise_or(a, b))


def _reduce_combined(combined: Image.Image) -> Image.Image:
    """Mengepres sub-piksel horizontal (w*2) kembali menjadi ukuran asli (w) tanpa distorsi matematika"""
    arr = _to_bin(combined)
    h, full_w = arr.shape
    if full_w % 2 != 0:
        raise ValueError("Combined image width must be even")
    w = full_w // 2
    pairs = arr.reshape(h, w, 2)
    # Logika: Dianggap hitam (1) jika kedua pasang sub-piksel bernilai hitam (1)
    reduced = (pairs.sum(axis=-1) == 2).astype(np.uint8)
    return _to_pil(reduced)


def _cv2_decode(image: Image.Image) -> str | None:
    arr = np.array(image.convert("L"), dtype=np.uint8)
    data, _points, _ = _QR_DETECTOR.detectAndDecode(arr)
    return data if data else None


def run_visual_crypto_flow(recovery_share_encoded: str, username: str) -> None:
    """Fungsi utama pengendali alur pembuatan Visual Cryptography dari sisi Client"""
    print("\n" + "="*60)
    display_info(f"[ALUR BONUS] Pemrosesan Citra QR Code untuk user: {username}")
    print("="*60)
    
    main_qr_img = recovery_share_to_qr(recovery_share_encoded)
    display_success("QR Code utama berhasil dibuat.")
    
    user_dir = Path(f"data/client/vc_{username}")
    user_dir.mkdir(parents=True, exist_ok=True)
    
    main_qr_path = user_dir / "recovery_qr_original.png"
    if confirm_action("Apakah Anda ingin MENYIMPAN gambar QR utuh/jadi ini ke folder vc_user?"):
        main_qr_img.save(main_qr_path)
        display_success(f"Berkas QR utama disimpan di: {main_qr_path}")
    else:
        display_info("Berkas QR utama diabaikan (tidak disimpan ke folder lokal).")

    print("\n[PROSES] Memecah citra QR utama menjadi visual shares terdistribusi...")
    s1, s2 = split_qr_visual(main_qr_img)
    
    path_share1 = user_dir / "share1.png"
    path_share2 = user_dir / "share2.png"
    
    s1.save(path_share1)
    s2.save(path_share2)
    
    print(f"[OTOMATIS] Komponen Visual Cryptography selalu dibuat & disimpan:")
    print(f"           -> {path_share1}")
    print(f"           -> {path_share2}")
    display_success("Visual cryptography split shares berhasil diamankan ke folder lokal.")
    print("="*60 + "\n")


def run_reconstruct_flow(username: str) -> str | None:
    """
    [DISAMAKAN] Membaca share1 dan share2, menggabungkan, mereduksi noise piksel melar,
    lahu memindai otomatis string Recovery Share di dalamnya.
    """
    user_dir = Path(f"data/client/vc_{username}")
    path_share1 = user_dir / "share1.png"
    path_share2 = user_dir / "share2.png"
    
    if not path_share1.exists() or not path_share2.exists():
        display_error("Gagal Rekonstruksi: Berkas share1.png atau share2.png tidak ditemukan!")
        return None
        
    print("\n" + "="*60)
    display_info(f"[PROSES REKONSTRUKSI] Memuat komponen gambar untuk: {username}")
    
    s1 = Image.open(path_share1)
    s2 = Image.open(path_share2)
    
    # 1. Tumpuk/Gabungkan gambar biner
    combined_img = combine_qr_visual(s1, s2)
    
    # 2. Coba deteksi langsung pada hasil tumpukan awal
    data = _cv2_decode(combined_img)
    
    # 3. Jika gagal (karena rasio melar 2x), jalankan fungsi reduksi sub-piksel cerdas Anda
    if not data:
        try:
            reduced_img = _reduce_combined(combined_img)
            # Simpan hasil reduksi yang bersih ke folder user untuk bukti laporan/pengujian
            reconstructed_path = user_dir / "reconstructed_qr.png"
            reduced_img.save(reconstructed_path)
            display_success(f"Citra QR hasil reduksi disalin ke: {reconstructed_path}")
            
            data = _cv2_decode(reduced_img)
        except Exception as e:
            display_error(f"Gagal melakukan proses reduksi citra: {e}")
            return None
            
    if data:
        display_success("Matriks QR Code BERHASIL dipindai secara akurat!")
        print(f"[DATA DITEMUKAN] Recovery Share String:\n{data}")
        print("="*60 + "\n")
        return data
    else:
        display_error("QR Code terdeteksi namun strukturnya rusak atau gagal dipindai oleh dekoder OpenCV.")
        print("="*60 + "\n")
        return None