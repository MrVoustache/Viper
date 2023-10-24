"""
This module adds some useful minor tools for debug.
"""


from typing import Any

__all__ = ["TimedPrint"]





class TimedPrint:

    """
    Generates a print function that only prints if the delay between two of its outputs has been longer that the configures delay.
    Example:
    >>> printer = TimedPrint(2.0)
    >>> printer("Hello World")
    Hello World
    >>> printer("Hey")  # Only prints "Hey" if 2 seconds have passed since the last call to printer.
    """

    def __init__(self, delay : float = 5.0) -> None:
        from time import time_ns
        self.__timer = time_ns
        self.__t = time_ns()
        self.__enabled : bool = True
        self.set(delay)

    @property
    def enabled(self) -> bool:
        """
        This TimedPrint instance will only print if this value is True.
        """
        return self.__enabled
    
    @enabled.setter
    def enabled(self, value : bool):
        if not isinstance(value, bool):
            raise TypeError(f"Expected bool, got '{type(value).__name__}'")
        self.__enabled = value
    
    def __call__(self, *args: Any, **kwargs : Any) -> None:
        if self.enabled and (self.__timer() - self.__t) > self.__delay:
            print(*args, **kwargs)
            self.__t = self.__timer()
    
    def reset(self):
        """
        Sets timer to 0 (as if something just had been printed).
        """
        self.__t = self.__timer()

    def clear(self):
        """
        Clears timer (as if the last print was long ago enough).
        """
        self.__t = self.__timer() - 2 * self.__delay
    
    def set(self, delay : float):
        """
        Sets the minimum delay to given value (in seconds).
        """
        self.__delay = round(delay * 1000000000)





del Any