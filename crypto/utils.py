"""
This module contains some cryptographic utilities.
"""

__all__ = ["generate_salt", "derive_passphrase"]





def generate_salt() -> bytes:
    """
    Generates a 256 bits random salt.
    """
    from os import urandom
    return urandom(32)

def derive_passphrase(passphrase : str | bytes | bytearray | memoryview, *, salt : bytes | bytearray | memoryview | None = None, size : int = 32, power_factor : float = 1.0) -> bytes:
    """
    Derives a key from a password using PBKDF2HMAC.
    If salt is ommited, it is randomly generated using urandom.
    The salt is not returned. If you need it, use generate_salt().
    The power_factor is a multiplicative factor over the computation time. Changing it changes the derived keys!
    """
    if isinstance(passphrase, str):
        passphrase = passphrase.encode("utf-8")
    if not isinstance(passphrase, bytes | bytearray | memoryview):
        raise TypeError("Expected str, or readable bytes buffer, got " + repr(type(passphrase).__name__))
    if salt == None:
        salt = generate_salt()
    if not isinstance(salt, bytes | bytearray | memoryview):
        raise TypeError("Expected readable bytes buffer for salt, got " + repr(type(salt).__name__))
    if not isinstance(size, int):
        raise TypeError("Expected int for size, got " + repr(type(size).__name__))
    if size <= 0:
        raise ValueError("Expected positive nonzero size, got " + repr(size))
    try:
        power_factor = float(power_factor)
    except:
        pass
    if not isinstance(power_factor, float):
        raise TypeError("Expected float for power_factor, got " + repr(type(power_factor).__name__))
    if power_factor <= 0:
        raise ValueError("Expected positive nonzero power_factor, got " + repr(power_factor))

    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    deriver = PBKDF2HMAC(hashes.SHA512(), size, salt, round(500000 * power_factor))
    return deriver.derive(passphrase)