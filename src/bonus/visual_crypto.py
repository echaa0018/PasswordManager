from pathlib import Path
import cv2
import numpy as np
import qrcode
from PIL import Image

_QR_DETECTOR = cv2.QRCodeDetector()


def recovery_share_to_qr(share_str: str, box_size: int = 10, border: int = 4) -> Image.Image:
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
    src = _to_bin(qr_image)
    h, w = src.shape
    rng = np.random.default_rng()

    pick = rng.integers(0, 2, size=(h, w), dtype=np.uint8)
    pattern_a = np.stack([pick, 1 - pick], axis=-1)
    pattern_b = np.where(src[..., None] == 1, 1 - pattern_a, pattern_a)

    share1 = pattern_a.reshape(h, w * 2)
    share2 = pattern_b.reshape(h, w * 2)
    return _to_pil(share1), _to_pil(share2)


def combine_qr_shares(share1: Image.Image, share2: Image.Image) -> Image.Image:
    a = _to_bin(share1)
    b = _to_bin(share2)
    if a.shape != b.shape:
        raise ValueError("Shares must have identical dimensions")
    return _to_pil(np.bitwise_or(a, b))


def _reduce_combined(combined: Image.Image) -> Image.Image:
    arr = _to_bin(combined)
    h, full_w = arr.shape
    if full_w % 2 != 0:
        raise ValueError("Combined image width must be even")
    w = full_w // 2
    pairs = arr.reshape(h, w, 2)
    reduced = (pairs.sum(axis=-1) == 2).astype(np.uint8)
    return _to_pil(reduced)


def _cv2_decode(image: Image.Image) -> str | None:
    arr = np.array(image.convert("L"), dtype=np.uint8)
    data, _points, _ = _QR_DETECTOR.detectAndDecode(arr)
    return data if data else None


def decode_qr_image(image: Image.Image) -> str | None:
    direct = _cv2_decode(image)
    if direct:
        return direct
    try:
        reduced = _reduce_combined(image)
    except Exception:
        return None
    return _cv2_decode(reduced)


def save_shares(
    share1: Image.Image,
    share2: Image.Image,
    out_dir: str | Path = "data/client/",
) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    p1 = out_dir / "share1.png"
    p2 = out_dir / "share2.png"
    share1.save(p1)
    share2.save(p2)
    return p1, p2