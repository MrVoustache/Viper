"""
This module contains some cryptographic utilities.
"""

__all__ = ["generate_salt", "derive_passphrase", "ask_user_passphrase", "ask_user_passphrase_twice"]





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

def ask_user_passphrase(message : str = "Enter passphrase > ") -> str:
    """
    Requests a passphrase to the user.
    Prints message before letting the user type their passphrase (without newline).
    """
    if not isinstance(message, str):
        raise TypeError("Expected str, got " + repr(type(message).__name__))
    from getpass import getpass
    return getpass(message)

class StupidUser(Exception):

    """
    The current user is stupid.
    """

def ask_user_passphrase_twice(message : str = "Enter passphrase > ", confirm_message : str = "Re-enter the same passphrase > ", failure_message : str = "The passphrase did not match. Enter a new passphrase > ", max_attempts : int = 3) -> str:
    """
    Same as ask_user_passphrase, but asks confirmation but requirering the user to type the same passphrase again.
    confirm_message is typed after the first input, after a newline and before the second input.
    If the two passphrases do not match, restarts the process but message is replaced by failure_message.
    At most max_attempts will be made.
    """
    if not isinstance(message, str) or not isinstance(confirm_message, str) or not isinstance(failure_message, str) or not isinstance(max_attempts, int):
        raise TypeError("Expected str, str, str, int, got " + repr(type(message).__name__) + ", " + repr(type(confirm_message).__name__) + ", " + repr(type(failure_message).__name__) + " and " + repr(type(max_attempts).__name__))
    if max_attempts <= 0:
        raise TypeError("Expected positive nonzero integer for max_attempts, got " + repr(max_attempts))
    
    p1 = ask_user_passphrase(message)
    p2 = ask_user_passphrase(confirm_message)

    n = 1
    while p1 != p2:
        p1 = ask_user_passphrase(failure_message)
        p2 = ask_user_passphrase(confirm_message)
        if p1 == p2:
            break
        n += 1
        if n >= max_attempts:
            raise StupidUser("The user was not able to write the same passphrase twice after {} attempts...Bro!".format(n))
    
    return p1