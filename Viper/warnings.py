"""
This module adds a few more useful warning classes to Python.
"""

from warnings import simplefilter

__all__ = ["SecurityWarning", "VulnerabilityWarning"]





class SecurityWarning(Warning):

    """
    This class indicates that some bare security requirements could not be met.
    """

simplefilter("default", SecurityWarning)



class VulnerabilityWarning(SecurityWarning):

    """
    This class indicates that a vulnerability just appeared in the executing code and could be (or has been) used by an attacker.
    """

simplefilter("default", VulnerabilityWarning)



del simplefilter