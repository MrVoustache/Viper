"""
This module contains some useful string formatting tools.
"""


__all__ = ["byte_size", "bit_size", "duration"]




def byte_size(num : int) -> str:
    """
    Returns a string representing the approximated number in adapted order of bytes magnitude.
    """
    for unit in ['','K','M','G','T','P','E','Z']:
        if abs(num) < 1024:
            return "%3.2f%s%s" % (num, unit, "B")
        num /= 1024
    return "%.2f%s%s" % (num, 'Y', "B")


def bit_size(num : int) -> str:
    """
    Returns a string representing the approximated number in adapted order of bits magnitude.
    """
    for unit in ['','K','M','G','T','P','E','Z']:
        if abs(num) < 1024:
            return "%3.2f%s%s" % (num, unit, "b")
        num /= 1024
    return "%.2f%s%s" % (num, 'Y', "b")


def duration(time : float | int, smooth : bool = True) -> str:
    """
    Takes a duration (in seconds if float, nanoseconds if int) and returns a string representing this duration with appropriate units.
    If smooth is True, only the 2 most significant units will be taken.
    """
    units = {
        "year" : 365 * 24 * 60 * 60 * 10 ** 9,
        "d" : 24 * 60 * 60 * 10 ** 9,
        "h" : 60 * 60 * 10 **9,
        "min" : 60 * 10 ** 9,
        "s" : 10 ** 9,
        "ms" : 10 ** 6,
        "µs" : 10 ** 3,
        "ns" : 1
    }

    if isinstance(time, float):
        time = round(time * 10 ** 9)
    if not isinstance(time, int):
        raise TypeError("Expected int or float, got " + repr(time.__class__.__name__))
    if not isinstance(smooth, bool):
        raise TypeError("Expected bool for smooth, got " + repr(smooth.__class__.__name__))

    s = ""
    if time < 0:
        s += "-"
        time = -time
    if time == 0:
        return "0s"
    u = 0
    for unit, amount in units.items():
        n = time // amount
        time -= n * amount
        if n:
            s += str(n) + unit + ", "
            u += 1
        if smooth and u >= 2:
            break
    
    return s[:-2]