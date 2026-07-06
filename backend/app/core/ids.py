from nanoid import generate

_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def generate_id() -> str:
    """Short, random, non-sequential ID (12 chars) — used as the PK for every table.

    Sequential integer IDs let anyone probe neighboring records (/branches/2, /branches/3, ...);
    random IDs close that off. Alphabet excludes visually ambiguous characters (0/O, 1/l/I).
    """
    return generate(alphabet=_ALPHABET, size=12)
