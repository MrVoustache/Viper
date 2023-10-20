"""
This module adds a few useful class decorators to Python as well as an ABC for decorators.
"""

from abc import ABCMeta, abstractmethod
from typing import Any, Callable, Concatenate, Generic, TypeVar, ParamSpec, overload
from weakref import WeakValueDictionary

__all__ = ["Decorator", "semistaticmethod", "hybridmethod", "staticproperty"]





P1 = ParamSpec("P1")
R1 = TypeVar("R1")
P2 = ParamSpec("P2")
R2 = TypeVar("R2")

class Decorator(Generic[P1, R1, P2, R2], metaclass = ABCMeta):

    """
    This decorator class fixes the pickling problem encountered when creating a decorator class.
    Just use it as a base class for you decorator classes.
    """

    from pickle import dumps as __dumps, PicklingError as __PicklingError
    from functools import WRAPPER_ASSIGNMENTS as __WRAPPER_ASSIGNMENTS
    from importlib import import_module
    __import_module = staticmethod(import_module)
    del import_module

    def __init__(self, func : Callable[P1, R1]) -> None:
        if not callable(func):
            raise TypeError(f"Expected callable, got '{type(func).__name__}'")
        for name in Decorator.__WRAPPER_ASSIGNMENTS:
            setattr(self, name, getattr(func, name, None))
        self.__wrapped__ = func

    def __set_name__(self, owner : type, name : str):
        self.__name__ = name
        self.__qualname__ = f"{owner.__qualname__}.{name}"
        self.__module__ = owner.__module__

    @abstractmethod
    def __call__(self, *args: P2.args, **kwds: P2.kwargs) -> R2:
        raise NotImplementedError
    
    def __is_target_pickable(self) -> bool:
        """
        Internal function that checks if the wrapped target is itself pickable.
        """
        try:
            Decorator.__dumps(self.__wrapped__)
            return True
        except Decorator.__PicklingError:
            return False
        
    def __is_global(self) -> bool:
        """
        Internal function that checks if the decorator is the global value referenced by target's path.
        """
        if self.__module__ is None or self.__qualname__ is None:
            print("What???")
            return False
        mod = Decorator.__import_module(self.__module__)
        qualname = self.__qualname__
        obj, qualname = getattr(mod, qualname.partition(".")[0]), qualname.partition(".")[2]
        while qualname:
            obj, qualname = getattr(obj, qualname.partition(".")[0]), qualname.partition(".")[2]
        return obj is self
    
    @staticmethod
    def _global_load(module : str, qualname : str) -> "Decorator":
        """
        Internal function used to load a decorated object from a fully qualified module and name.
        """
        mod = Decorator.__import_module(module)
        obj, qualname = getattr(mod, qualname.partition(".")[0]), qualname.partition(".")[2]
        while qualname:
            obj, qualname = getattr(obj, qualname.partition(".")[0]), qualname.partition(".")[2]
        return obj
    
    def __reduce__(self) -> str | tuple[Any, ...]:
        if self.__is_global():
            return self._global_load, (self.__module__, self.__qualname__)
        elif self.__is_target_pickable():
            return super().__reduce__()
        else:
            raise Decorator.__PicklingError("Unpickable decorated object")
        
del P1, R1, P2, R2





P = ParamSpec("P")
R = TypeVar("R")
T = TypeVar("T")

class semistaticmethod(Decorator[Concatenate[T | None, P], R, P, R]):

    """
    This decorator makes a function behave like a method when called from a class instance, but when called from the class, the "self" argument will be None.
    You might have to annotate the method parameter with the right type to pass the type checkers.
    """

    from types import MethodType as __MethodType



    class NullMethod:

        """
        Like a method, but bound to None.
        """

        def __init__(self, func : Callable[Concatenate[T | None, P], R]) -> None:
            self.__func = func

        def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
            return self.__func(None, *args, **kwargs)
        
        def __repr__(self) -> str:
            address = hex(id(self.__func))[2:].upper()
            address = "0x" + ("0" * (16 - len(address))) + address
            return f"<null-bound method {self.__func.__qualname__} at {address}>"
        

    
    def __repr__(self) -> str:
        address = hex(id(self.__wrapped__))[2:].upper()
        address = "0x" + ("0" * (16 - len(address))) + address
        return f"<semistaticmethod {self.__wrapped__.__qualname__} at {address}>"

    def __call__(self, instance : T | None, *args : P.args, **kwargs : P.kwargs) -> R:
        return self.__wrapped__(instance, *args, **kwargs)
    
    @overload
    def __get__(self, obj : T , cls : type[T] | None = None) -> Callable[P, R]:
        ...

    @overload
    def __get__(self, obj : None, cls : type[T]) -> Callable[P, R]:
        ...

    def __get__(self, obj : T | None, cls : type[T] | None = None) -> Callable[P, R]:
        if obj is not None:
            return semistaticmethod.__MethodType(self, obj)
        else:
            return semistaticmethod.NullMethod(self)





class hybridmethod(Decorator[Concatenate[T | type[T], P], R, P, R]):

    """
    This decorator makes a function behave like a method when called from a class instance, and as a classmethod when called from a class.
    You might have to annotate the method parameter with the right type to pass the type checkers.
    """

    from types import MethodType as __MethodType
    
    def __repr__(self) -> str:
        address = hex(id(self.__wrapped__))[2:].upper()
        address = "0x" + ("0" * (16 - len(address))) + address
        return f"<hybridmethod {self.__wrapped__.__qualname__} at {address}>"

    def __call__(self, instance_or_class : T | type[T], *args : P.args, **kwargs : P.kwargs) -> R:
        return self.__wrapped__(instance_or_class, *args, **kwargs)

    @overload
    def __get__(self, obj : None, cls : type[T] | None = None) -> Callable[P, R]:
        ...

    @overload
    def __get__(self, obj : T, cls : type[T]) -> Callable[P, R]:
        ...
    
    def __get__(self, obj : T | None, cls : type[T] | None = None) -> Callable[P, R]:
        if obj is not None:
            return hybridmethod.__MethodType(self, obj)
        else:
            return hybridmethod.__MethodType(self, cls)
    




class staticproperty(property, Generic[P, R, T]):

    """
    This decorator transforms a method into a static property of the class (it takes no self/cls argument).
    You can use setter, getter and deleter to set the different staticproperty descriptors.
    Note that for now, only the getter will work when called from the class.
    """

    def __init__(self, fget : Callable[[], R] | None = None, fset : Callable[[R], None] | None = None, fdel : Callable[[], None] | None = None, *args) -> None:
        self.__fget : "Callable[[], R] | None" = None
        self.__fset : "Callable[[R], None] | None" = None
        self.__fdel : "Callable[[], None] | None" = None
        if fget != None:
            self.__fget = staticmethod(fget)
        if fset != None:
            self.__fset = staticmethod(fset)
        if fdel != None:
            self.__fdel = staticmethod(fdel)
        self.__name__ : str = ""
        self.__cls__ : type | None = None

    @property
    def fget(self) -> Callable[[], R] | None:
        """
        The getter function of this staticproperty.
        """
        return self.__fget
    
    @property
    def fset(self) -> Callable[[R], None] | None:
        """
        The setter function of this staticproperty.
        """
        return self.__fset
    
    @property
    def fdel(self) -> Callable[[], None] | None:
        """
        The deleter function of this staticproperty.
        """
        return self.__fdel
    
    def __set_name__(self, cls : type[T], name : str):
        self.__name__ = name
        self.__cls__ = cls

    def __repr__(self) -> str:
        if self.__name__ and self.__cls__:
            return f"<staticproperty {self.__name__} of class '{self.__cls__}'>"
        address = hex(id(self))[2:].upper()
        address = "0x" + ("0" * (16 - len(address))) + address
        return f"<staticproperty at {address}"
    
    def __get__(self, obj : T | None, cls : type[T] | None = None) -> R:
        if not self.__fget:
            raise AttributeError("staticproperty '{}' of '{}' {} has not getter".format(self.__name__, self.__cls__, "object" if obj is not None else "class"))
        try:
            return self.__fget()
        except AttributeError as e:
            raise e from None
    
    def __set__(self, obj : T | None, value : R):
        if not self.__fset:
            raise AttributeError("staticproperty '{}' of '{}' {} has not setter".format(self.__name__, self.__cls__, "object" if obj is not None else "class"))
        try:
            return self.__fset(value)
        except AttributeError as e:
            raise e from None
    
    def __delete__(self, obj : T | None):
        if not self.__fdel:
            raise AttributeError("staticproperty '{}' of '{}' {} has not deleter".format(self.__name__, self.__cls__, "object" if obj is not None else "class"))
        try:
            return self.__fdel()
        except AttributeError as e:
            raise e from None
        
    def getter(self, fget : Callable[[], R]) -> "staticproperty":
        """
        Descriptor to obtain a copy of the staticproperty with a different getter.
        """
        self.__fget = staticmethod(fget)
        return self
    
    def setter(self, fset : Callable[[R], None]) -> "staticproperty":
        """
        Descriptor to obtain a copy of the staticproperty with a different setter.
        """
        self.__fset = staticmethod(fset)
        return self
    
    def deleter(self, fdel : Callable[[], None]) -> "staticproperty":
        """
        Descriptor to obtain a copy of the staticproperty with a different deleter.
        """
        self.__fdel = staticmethod(fdel)
        return self
    
del P, R, T





del ABCMeta, abstractmethod, Any, Callable, Concatenate, Generic, TypeVar, ParamSpec, overload, WeakValueDictionary