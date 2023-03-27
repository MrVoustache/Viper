"""
This module contains some tools to clean/modify importation of modules.
"""


from typing import Any, Optional
from types import ModuleType

__all__ = ["replace_module", "get_if_imported", "clean_annotations"]





def replace_module(name : str, value : Any):
    """
    Replaces the module with given name by value.
    Warning : this is permanent during the lifetime of this interpreter or until the given module gets forcefully reloaded.
    For example, a module which only contains a class with the same name might be replaced by the class itself.
    """
    if not isinstance(name, str):
        raise TypeError("Name must be a str, got "+repr(name.__class__.__name__))
    import sys
    if name not in sys.modules:
        raise KeyError("Module has not been loaded (nor pre-loaded)")
    sys.modules[name] = value


def get_if_imported(module : str) -> ModuleType:
    """
    Returns the module if it has been loaded.
    Raises ModuleNotFoundError otherwise.
    """
    if module.__class__ != str:
        raise TypeError("Expected str, got "+repr(module.__class__.__name__))
    import sys
    if module in sys.modules:
        return sys.modules[module]
    raise ModuleNotFoundError("Module '{}' has not been imported yet".format(module))


def clean_annotations(*clss : type) -> None:
    """
    Cleans the annotations of objects in a class (or classes) :
    Replaces the class name as str by the actual class.

    Example:

    >>> class Foo:
    ... def new(self) -> 'Foo':
    ...     ...
    ...
    >>> clean_annotations(Foo)
    >>> print(Foo.new.__annotations__)
    {'return': <class '__main__.Foo'>}

    When given multiple classes, it will also clean them globally (cleaning the occurences of each class into each other).
    """
    for cls in clss:
        if not isinstance(cls, type):
            raise TypeError("Expected class, got "+repr(cls.__class__.__name__))
    

    def clean_typing(t, name, value):
        from typing import _GenericAlias, ForwardRef
        if t == name or t == ForwardRef(name):
            t = value
        elif isinstance(t, _GenericAlias) and hasattr(t, "__args__"):
            t.__args__ = tuple(clean_typing(ti, name, value) for ti in t.__args__)
        return t
    
    work = set()
    for cls in clss:
        l = [getattr(cls, att) for att in dir(cls)]
        for obj in filter(lambda obj: not isinstance(obj, type), l):
            try:
                work.add(obj)
            except:
                pass
    work.update(clss)

    for cls in clss:

        name = cls.__name__

        for obj in filter(lambda obj: hasattr(obj, "__annotations__"), work):
            for k, ann in obj.__annotations__.items():
                obj.__annotations__[k] = clean_typing(ann, name, cls)





del Any, Optional, ModuleType