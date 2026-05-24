import secrets
from itertools import combinations
import pytest
from crypto.shamir import combine_shares, split_secret


def test_split_returns_three_shares():
    secret = secrets.token_bytes(16)
    shares = split_secret(secret)
    assert len(shares) == 3
    for idx, share in shares:
        assert isinstance(idx, int)
        assert isinstance(share, bytes)


def test_any_two_of_three_reconstruct():
    secret = secrets.token_bytes(16)
    shares = split_secret(secret)
    for combo in combinations(shares, 2):
        assert combine_shares(list(combo)) == secret


def test_all_three_reconstruct():
    secret = secrets.token_bytes(16)
    shares = split_secret(secret)
    assert combine_shares(shares) == secret


def test_single_share_rejected():
    secret = secrets.token_bytes(16)
    shares = split_secret(secret)
    with pytest.raises(ValueError):
        combine_shares([shares[0]])


def test_invalid_secret_length():
    with pytest.raises(ValueError):
        split_secret(b"too_short")


def test_invalid_threshold():
    with pytest.raises(ValueError):
        split_secret(secrets.token_bytes(16), threshold=1, shares=3)