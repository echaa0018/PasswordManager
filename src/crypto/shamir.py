from Crypto.Protocol.SecretSharing import Shamir
DEFAULT_THRESHOLD = 2
DEFAULT_SHARES = 3


def split_secret(
    secret: bytes,
    threshold: int = DEFAULT_THRESHOLD,
    shares: int = DEFAULT_SHARES,
) -> list[tuple[int, bytes]]:
    if len(secret) != 16:
        raise ValueError(f"Secret must be exactly 16 bytes, got {len(secret)}")
    if threshold < 2 or threshold > shares:
        raise ValueError("Threshold must satisfy 2 <= threshold <= shares")
    return Shamir.split(threshold, shares, secret)


def combine_shares(shares: list[tuple[int, bytes]]) -> bytes:
    if len(shares) < 2:
        raise ValueError("Need at least 2 shares to combine")
    return Shamir.combine(shares)