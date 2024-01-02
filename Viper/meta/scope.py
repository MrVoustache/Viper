"""
This module adds the StackContext class that allows for objects declared in context managers to be found at any stack levels.
"""

from types import CodeType, FrameType, TracebackType
from typing import Literal, Self

__all__ = ["ScopeContext", "active"]





class ScopeContext:

    """
    Classes inhereting from this class will be usable in "with" statements and "active" instances can be listed/tested at any scope level.
    These scopes include all code executed by the current thread that is after entering a "with" statement and before exiting the corresponding block.

    Example:
    >>> from Viper.meta.scope import *
    >>> sc = ScopeContext()
    >>> def is_active():
    ...     print("active" if sc.is_active() else "inactive")
    ... 
    >>> is_active()
    inactive
    >>> with sc:
    ...     is_active()
    ... 
    active
    >>> def gen():
    ...     while True:
    ...         yield
    ...         is_active()
    ...
    >>> g = gen()
    >>> next(g)
    >>> next(g)
    inactive
    >>> with sc:
    ...     next(g)
    ... 
    active
    >>> def with_sc(f, *args, **kwargs):
    ...     with sc:
    ...         return f(*args, **kwargs)
    ... 
    >>> from threading import Thread
    >>> Thread(target = next, args = (g, )).start()
    inactive
    >>> with sc:
    ...     t = Thread(target = next, args = (g, ))
    ...     t.start()
    ...     t.join()            # Prints "inactive" as the main thread is not the one calling is_active() while it is the one in the activation scope.
    ...
    inactive
    >>> Thread(target = with_sc, args = (next, g)).start()      # Here, the active scope is in the good Thread
    active

    Note though that a scope can be passed on between Threads:
    >>> def with_gen():
    ...     with sc:
    ...         while True:
    ...             yield
    ...             is_active()
    ...
    >>> g = with_gen()
    >>> next(g)
    >>> next(g)
    active
    >>> Thread(target = next, args = (g, )).start()     # Scope was never exited in the generator g
    active

    To keep this functionnality in subclasses, just call super().__enter__ and super().__exit__ when subclassing these methods.
    """

    from inspect import stack
    __stack = staticmethod(stack)
    del stack

    __active : "dict[int, tuple[ScopeContext, list[CodeType]]]" = {}
    __cls_enter : "dict[type[ScopeContext], CodeType]" = {}
    __cls_exit : "dict[type[ScopeContext], CodeType]" = {}

    def __init_subclass__(cls) -> None:
        ScopeContext.__cls_enter[cls] = cls.__enter__.__code__
        ScopeContext.__cls_exit[cls] = cls.__exit__.__code__

    def __find_matching_context(self, name : Literal["__enter__", "__exit__"]) -> FrameType | None:
        """
        Internal function used to find the frame of the matching scope.
        """
        if name == "__enter__":
            for si in ScopeContext.__stack():
                if si.frame.f_code is ScopeContext.__cls_enter.get(type(self), ScopeContext.__enter__.__code__):
                    return si.frame.f_back
        else:
            for si in ScopeContext.__stack():
                if si.frame.f_code is ScopeContext.__cls_exit.get(type(self), ScopeContext.__exit__.__code__):
                    return si.frame.f_back

    def __enter__(self) -> Self:
        """
        Implements with self. Activates the object for the whole scope (or just increment its activation level).
        """
        i = id(self)
        s = self.__find_matching_context("__enter__")
        if s is None:
            raise RuntimeError("Could not resolve frames to find first context __enter__")
        ScopeContext.__active.setdefault(i, (self, []))[1].append(s.f_code)
        return self
    
    def __exit__(self, exc_type : type[BaseException] | None, exc_value : BaseException | None, traceback : TracebackType | None):
        """
        Implements with self. Deactivates the object for the whole scope (or just decrement its activation level).
        """
        i = id(self)
        s = self.__find_matching_context("__exit__")
        if s is None:
            raise RuntimeError("Could not resolve frames to find first context __exit__")
        if i not in ScopeContext.__active:
            raise RuntimeError("Exiting context without a call to '__enter__'")
        _, codes = ScopeContext.__active[i]
        for j, c in enumerate(codes):
            if c is s.f_code:
                codes.pop(j)
                break
        else:
            raise RuntimeError("Could not find associated code object used to enter context")
        if not codes:
            ScopeContext.__active.pop(i)

    def is_active(self) -> bool:
        """
        Returns True if the object is active in any upper context.
        (i.e. if there exists any stack level higher than the current that in inside of a "with self".)
        """
        i = id(self)
        if i not in ScopeContext.__active:
            return False
        current_codes = [si.frame.f_code for si in ScopeContext.__stack()]
        _, codes = ScopeContext.__active[i]
        for i, c1 in enumerate(codes):
            for c2 in current_codes:
                if c1 is c2:
                    return True
        return False
    
    @classmethod
    def list_active(cls) -> list[Self]:
        """
        Lists all the active instances of this class in the current stack.
        """
        return [self for i, (self, codes) in ScopeContext.__active.items() if isinstance(self, cls) and self.is_active()]
            
    



def active() -> list[ScopeContext]:
    """
    Returns all the active objects in the current stack.
    """
    return ScopeContext.list_active()





del CodeType, FrameType, TracebackType, Self