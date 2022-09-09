"""
This module introduces sessions, which are used to store active keys in the session context.
Cryptography primitives may create sessions per module to ease usage of security.
"""

from typing import Iterator

__all__ = ["SecuritySession"]





class SecuritySession:

    """
    A security session is a keychain in which you can put and access security keys and passwords/passphrases without saving them at any point.
    """

    def __init__(self, *, private : bool = True) -> None:
        if not isinstance(private, bool):
            raise TypeError("Expected bool for module_share, got " + repr(type(private).__name__))

        __keychain : set[bytes | str] = set()
        __named_keychain : dict[str, bytes | str] = {}

        from inspect import stack
        from typing import Iterator
        from Viper.crypto.exceptions import ForbiddenSessionAccess

        def module_stacktrace() -> list[str]:
            s = []
            for info in stack():
                name = info.filename
                if not s or s[-1] != name:
                    s.append(name)
            return s

        __user_stacktrace = module_stacktrace()

        def __keys() -> Iterator[bytes | str]:
            if private and __user_stacktrace != module_stacktrace():
                raise ForbiddenSessionAccess("Cannot access this SecuritySession from this module.")
            yield from __keychain
            yield from __named_keychain.values()

        def __add(value : bytes | str):
            if private and __user_stacktrace != module_stacktrace():
                raise ForbiddenSessionAccess("Cannot access this SecuritySession from this module.")
            __keychain.add(value)
        
        def __get(name : str) -> bytes:
            if private and __user_stacktrace != module_stacktrace():
                raise ForbiddenSessionAccess("Cannot access this SecuritySession from this module.")
            if name not in __named_keychain:
                raise KeyError("No key with this name.")
            return __named_keychain[name]
        
        def __set(name : str, value : bytes | str | None):
            if private and __user_stacktrace != module_stacktrace():
                raise ForbiddenSessionAccess("Cannot access this SecuritySession from this module.")
            if isinstance(value, bytes | str):
                __named_keychain[name] = value
            if value == None:
                if name in __named_keychain:
                    __named_keychain.pop(name)
        
        def __clear():
            if private and __user_stacktrace != module_stacktrace():
                raise ForbiddenSessionAccess("Cannot access this SecuritySession from this module.")
            __keychain.clear()
            __named_keychain.clear()
        
        self.__keys = __keys
        self.__add = __add
        self.__get = __get
        self.__set = __set
        self.__clear = __clear
        self.__private = private
    
    @property
    def private(self) -> bool:
        """
        True if the session is private. If it is, only use cases with the same module stacktrace as the one that created the session will be allowed.
        """
        return self.__private
    
    def __iter__(self) -> Iterator[bytes | str]:
        """
        Iterates over the keys in the session.
        """
        yield from self.__keys()
    
    def add(self, value : bytes | bytearray | memoryview | str):
        """
        Adds an unamed key to the session.
        """
        if not isinstance(value, bytes | bytearray | memoryview | str):
            raise TypeError("Expected readable bytes buffer or str for value, got " + repr(type(value).__name__))
        try:
            self.__add(bytes(value) if isinstance(value, bytearray | memoryview) else value)
        except BaseException as e:
            raise e.with_traceback(None) from None
    
    def __getitem__(self, name : str) -> bytes:
        """
        Returns the key with the given name.
        Raises KeyError if it does not exist in the session.
        """
        if not isinstance(name, str):
            raise TypeError("Expected str for name, got " + repr(type(name).__class__))
        try:
            return self.__get(name)
        except BaseException as e:
            raise e.with_traceback(None) from None
    
    def __setitem__(self, name : str, value : bytes | bytearray | memoryview | str):
        """
        Adds a named key to the session.
        """
        if not isinstance(name, str):
            raise TypeError("Expected str for name, got " + repr(type(name).__class__))
        if not isinstance(value, bytes | bytearray | memoryview | str):
            raise TypeError("Expected readable bytes buffer or str for value, got " + repr(type(value).__name__))
        try:
            return self.__set(name, bytes(value) if isinstance(value, bytearray | memoryview) else value)
        except BaseException as e:
            raise e.with_traceback(None) from None
    
    def __delitem__(self, name : str):
        """
        Removes a named key from the session.
        """
        if not isinstance(name, str):
            raise TypeError("Expected str for name, got " + repr(type(name).__class__))
        try:
            return self.__set(name, None)
        except BaseException as e:
            raise e.with_traceback(None) from None
    
    def clear(self):
        """
        Clears the sessions. All keys are deleted.
        """
        try:
            return self.__clear()
        except BaseException as e:
            raise e.with_traceback(None) from None




del Iterator