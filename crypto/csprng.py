import secrets
import string

CHARACTER_SETS = {
    "UPPER": string.ascii_uppercase,
    "LOWER": string.ascii_lowercase,
    "DIGITS": string.digits,
    "SYMBOLS": "!@#$%^&*()-_=+[]{};:,.<>?/|~",
}


def generate_password(
    length: int,
    use_upper: bool = True,
    use_lower: bool = True,
    use_digits: bool = True,
    use_symbols: bool = True,
) -> str:
    if length < 1:
        raise ValueError("Length must be at least 1")

    selected = []
    if use_upper:
        selected.append(CHARACTER_SETS["UPPER"])
    if use_lower:
        selected.append(CHARACTER_SETS["LOWER"])
    if use_digits:
        selected.append(CHARACTER_SETS["DIGITS"])
    if use_symbols:
        selected.append(CHARACTER_SETS["SYMBOLS"])

    if not selected:
        raise ValueError("At least one character category must be enabled")

    if length < len(selected):
        raise ValueError(
            f"Length {length} too short to include one char from each of "
            f"{len(selected)} selected categories"
        )

    password_chars = [secrets.choice(pool) for pool in selected]
    full_pool = "".join(selected)
    password_chars.extend(secrets.choice(full_pool) for _ in range(length - len(selected)))

    for i in range(len(password_chars) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        password_chars[i], password_chars[j] = password_chars[j], password_chars[i]

    return "".join(password_chars)