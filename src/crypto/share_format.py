import base64
import binascii
import json


def encode_share(index: int, share_bytes: bytes) -> str:
    payload = json.dumps({
        "index": index,
        "share": base64.b64encode(share_bytes).decode("ascii"),
    })
    return base64.b64encode(payload.encode("utf-8")).decode("ascii")


def decode_share(encoded: str) -> tuple[int, bytes]:
    try:
        payload = base64.b64decode(encoded.encode("ascii"), validate=True)
        obj = json.loads(payload.decode("utf-8"))
        index = int(obj["index"])
        share_bytes = base64.b64decode(obj["share"], validate=True)
    except (binascii.Error, ValueError, KeyError, json.JSONDecodeError, UnicodeDecodeError) as e:
        raise ValueError(f"Malformed share: {e}") from e
    return index, share_bytes


def encode_share_hex(index: int, share_bytes: bytes) -> str:
    return f"{index}:{share_bytes.hex()}"