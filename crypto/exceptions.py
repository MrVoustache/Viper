"""
This module adds some cryptography-related exceptions to Python.
"""

from Viper.exceptions import SecurityException

__all__ = ["AuthenticationError"]





class AuthenticationError(SecurityException):

    """
    This error indicates that the source of a given message is cannot be guaranteed.
    """


del SecurityException