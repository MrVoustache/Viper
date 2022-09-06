"""
This module adds a few base exceptions to Python.
"""

__all__ = ["SecurityException"]





class SecurityException(Exception):

    """
    This exception occurs when an important security property has been compromised.
    """