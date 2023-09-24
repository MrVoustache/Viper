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

    from pickle import dumps as __dumps

    __existing : WeakValueDictionary[tuple[str, str], "Decorator[P1, R1, P2, R2]"] = WeakValueDictionary()



    class _GlobalLoader:

        """
        Internal class used to load global names.
        """

        from inspect import getmodule
        __getmodule = staticmethod(getmodule)
        from importlib import import_module
        __import_module = staticmethod(import_module)
        from pickle import PicklingError as __PicklingError
        del getmodule, import_module

        __slots__ = {
            "__module" : "The complete name of the module in which the target was defined.",
            "__name" : "The complete name of the target in the module namespace."
        }

        def __init__(self, target : Callable[P2, R2]) -> None:
            module = type(self).__getmodule(target)
            if not module:
                raise ModuleNotFoundError(f"Cannot find the module {repr(target)} was defined in")
            self.__module = module.__name__
            name = target.__qualname__ if hasattr(target, "__qualname__") else (target.__name__ if hasattr(target, "__name__") else None)
            if name is None:
                for k, v in vars(module).items():       # Works at module level, if it was used to make a copy of a function under a different name.
                    if v is target:
                        name = k
                        break
            if name is None:
                raise NameError(f"Cannot find {repr(target)} in module '{module.__name__}'")
            obj = module
            try:
                for n in name.split("."):
                    obj = getattr(obj, n)
            except (NameError, KeyError, AttributeError):
                raise NameError(f"Cannot find {repr(target)} in module '{module.__name__}'")
            if obj is not target:
                raise type(self).__PicklingError(f"Cannot pickle {repr(target)}: it is not the same as {module.__name__}.{name}")
            self.__name = name
            if ":" in name or ":" in module.__name__:
                raise ValueError(f"Invalid global names function '{name}' in module '{module.__name__}'")

        def load(self) -> Callable[P1, R1]:
            """
            Loads the target.
            """
            mod = type(self).__import_module(self.__module)
            obj = mod
            try:
                for n in self.__name.split("."):
                    obj = getattr(obj, n)
            except (NameError, KeyError, AttributeError):
                raise NameError(f"Could not load '{self.__name}' from module '{self.__module}'")
            return obj
        
        def __getstate__(self) -> object:       # Just to make the pickle more compact
            return self.__module + ":" + self.__name
        
        def __setstate__(self, state : str):
            self.__module, self.__name = state.split(":")



    def __new__(cls, func : Callable[P1, R1]):
        if not callable(func):
            raise TypeError(f"Expected callable, got '{type(func).__name__}'")
        name = func.__qualname__ if hasattr(func, "__qualname__") else func.__name__
        module = func.__module__ if hasattr(func, "__module__") else None
        if name and module and (module, name) in cls.__existing:
            return cls.__existing[module, name]
        res = super().__new__(cls)
        if name and module:
            cls.__existing[module, name] = res
        return res

    def __init__(self, func : Callable[P1, R1]) -> None:
        if not callable(func):
            raise TypeError(f"Expected callable, got '{type(func).__name__}'")
        if func is not self:
            self.__wrapped__ = func

    def __set_name__(self, owner : type, name : str):
        self.__name__ = name
        self.__qualname__ = f"{owner.__qualname__}.{name}"
        self.__module__ = owner.__module__

    @abstractmethod
    def __call__(self, *args: P2.args, **kwds: P2.kwargs) -> R2:
        raise NotImplementedError
    
    def __reduce__(self) -> str | tuple[Any, ...]:
        try:
            Decorator.__dumps(self.__wrapped__)
        except:
            return Decorator._GlobalLoader(self).load, ()
        try:
            return Decorator._GlobalLoader(self).load, ()
        except:
            return super().__reduce__()
        
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
        


    def __init__(self, func : Callable[Concatenate[T | None, P], R]) -> None:
        super().__init__(func)
        self.__func = func
    
    def __repr__(self) -> str:
        address = hex(id(self.__func))[2:].upper()
        address = "0x" + ("0" * (16 - len(address))) + address
        return f"<semistaticmethod {self.__func.__qualname__} at {address}>"

    def __call__(self, instance : T | None, *args : P.args, **kwargs : P.kwargs) -> R:
        return self.__func(instance, *args, **kwargs)
    
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

    def __init__(self, func : Callable[Concatenate[T | type[T], P], R]) -> None:
        super().__init__(func)
        self.__func = func
    
    def __repr__(self) -> str:
        address = hex(id(self.__func))[2:].upper()
        address = "0x" + ("0" * (16 - len(address))) + address
        return f"<hybridmethod {self.__func.__qualname__} at {address}>"

    def __call__(self, instance_or_class : T | type[T], *args : P.args, **kwargs : P.kwargs) -> R:
        return self.__func(instance_or_class, *args, **kwargs)

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