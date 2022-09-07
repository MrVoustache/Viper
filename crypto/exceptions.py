"""
This module adds some cryptography-related exceptions to Python.
"""

from Viper.exceptions import SecurityException

__all__ = ["AuthenticationError", "InvalidKeyError", "ForbiddenSessionAccess"]





class AuthenticationError(SecurityException):

    """
    This error indicates that the source of a given message is cannot be guaranteed.
    """



class InvalidKeyError(SecurityException):

    """
    This error indicates that the key used for decryption is invalid.
    """



class ForbiddenSessionAccess(SecurityException, PermissionError):

    """
    This exception occurs when a module tries to access a private information which it doesn't own.
    """




del SecurityException