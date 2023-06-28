"""
This module adds metaclasses that make classes iterable, yielding all of their instances.
"""


from typing import Any, Generator, Sequence, TypeVar
from weakref import WeakValueDictionary

__all__ = ["InstanceReferencingClass", "InstancePreservingClass", "InstanceReferencingHierarchy", "InstancePreservingHierarchy"]





T = TypeVar("T")

class InstanceReferencingClass(type):

    """
    A metaclass for iterable classes.
    Classes with this metaclass will (weakly) store their instances, and you will be able to iterate over the class, yielding all its instances.
    Note: instances of this class should be hashable!

    Example:

    >>> class A(metaclass = InstanceReferencingClass):
    ...
    ...     def __init__(self, name : str):
    ...         self.name = name
    ...
    ...     def __str__(self) -> str:
    ...         return "A(" + self.name + ")"
    ...
    >>> a = A("a")
    >>> b = B("b")
    >>> print(list(A))
    [A(a), A(b)]
    >>> del a
    >>> print(list(A))
    [A(b)]
    >>> len(A)
    1
    """

    __instances : WeakValueDictionary[int, Any]

    def __new__(cls, name : str, bases : tuple[type], dct : dict):
        """
        Implements the creation of a new class
        """
        from .utils import signature_def, signature_call
        from typing import Iterable
        from functools import wraps
        from weakref import WeakValueDictionary

        s = WeakValueDictionary()
        
        def extract_slots(o : type) -> set[str]:
            if hasattr(o, "__slots__") and isinstance(o.__slots__, Iterable):   # type: ignore
                s = set(o.__slots__)                                            # type: ignore
            else:
                s = set()
            return s.union(*[extract_slots(b) for b in o.__bases__])

        added = False

        # Finding the __new__ method 
        old_new = None
        if "__new__" in dct:
            old_new = dct["__new__"]
        else:
            for b in bases:
                if hasattr(b, "__new__"):
                    old_new = getattr(b, "__new__")
        if old_new == None:
            old_new = object.__new__

        sig = "@wraps(old_target)\n"

        sig_def, env = signature_def(old_new, init_env = {"old_target" : old_new, "wraps" : wraps, "cls_dict" : s})
        
        code = sig + sig_def

        if old_new == object.__new__:       # Because object.__new__ says it would accept additional args passed to __init__, but in reality, it doesn't...
            code += "\n\tres = old_target(args[0])"
        else:
            code += "\n\tres = old_target(" + signature_call(old_new, decorate=False) + ")"

        code += "\n\tfrom builtins import id"

        code += "\n\tcls_dict[id(res)] = res"

        code += "\n\treturn res"

        exec(code, env)

        dct["__new__"] = env[old_new.__name__]

        # if this class has __slots__, then a __weakref__ slot is necessary
        if "__slots__" in dct and "__weakref__" not in dct["__slots__"] and not any("__weakref__" in extract_slots(b) for b in bases):
            added = True
            if isinstance(dct["__slots__"], dict):
                dct["__slots__"]["__weakref__"] = "The slot for the weakref of this object"
            elif isinstance(cls, (Sequence)):
                dct["__slots__"] = list(dct["__slots__"]) + ["__weakref__"]
        # Creating the class
        try:
            cls = super().__new__(cls, name, bases, dct)
        except TypeError:
            if added:   # The __weakref__ slot might be in a parent class
                dct["__slots__"].pop("__weakref__")
                cls = super().__new__(cls, name, bases, dct)
            else:
                raise
        # The Weakdict that will store all instances
        cls.__instances = s
        return cls
    
    def __iter__(self : type[T]) -> Generator[T, None, None]:
        """
        Implements the iteration over the class' instances
        """
        yield from tuple(self.__instances.values())
    
    def __len__(self) -> int:
        """
        Implements the len of this class (the number of existing instances)
        """
        return len(self.__instances)





class InstancePreservingClass(type):

    """
    Same as an InstanceReferencingClass, but instances are never deleted.
    Note: instances of this class should be hashable!

    Example:

    >>> class A(metaclass = InstancePreservingClass):
    ...
    ...     def __init__(self, name : str):
    ...         self.name = name
    ...
    ...     def __str__(self) -> str:
    ...         return "A(" + self.name + ")"
    ...
    >>> a = A("a")
    >>> b = B("b")
    >>> print(list(A))
    [A(a), A(b)]
    >>> del a
    >>> print(list(A))
    [A(a), A(b)]
    >>> len(A)
    2
    """

    def __new__(cls, name : str, bases : tuple[type], dct : dict):
        """
        Implements the creation of a new class
        """
        from .utils import signature_def, signature_call
        from functools import wraps

        s = []

        def extract_slots(o : type) -> set[str]:
            if not hasattr(o, "__slots__"):
                s = set()
            else:
                s = set(o.__slots__)
            return s.union(*[extract_slots(b) for b in o.__bases__])

        added = False

        # Finding the __new__ method 
        old_new = None
        if "__new__" in dct:
            old_new = dct["__new__"]
        else:
            for b in bases:
                if hasattr(b, "__new__"):
                    old_new = getattr(b, "__new__")
        if old_new == None:
            old_new = object.__new__

        sig = "@wraps(old_target)\n"

        sig_def, env = signature_def(old_new, init_env = {"old_target" : old_new, "wraps" : wraps, "cls_list" : s})
        
        code = sig + sig_def

        if old_new == object.__new__:       # Because object.__new__ says it would accept additional args passed to __init__, but in reality, it doesn't...
            code += "\n\tres = old_target(args[0])"
        else:
            code += "\n\tres = old_target(" + signature_call(old_new, decorate=False) + ")"

        code += "\n\tcls_list.append(res)"

        code += "\n\treturn res"

        exec(code, env)

        dct["__new__"] = env[old_new.__name__]
        
        # if this class has __slots__, then a __weakref__ slot is necessary
        if "__slots__" in dct and "__weakref__" not in dct["__slots__"] and not any("__weakref__" in extract_slots(b) for b in bases):
            added = True
            if isinstance(dct["__slots__"], dict):
                dct["__slots__"]["__weakref__"] = "The slot for the weakref of this object"
            elif isinstance(cls, (Sequence)):
                dct["__slots__"] = list(dct["__slots__"]) + ["__weakref__"]
        # Creating the class
        try:
            cls = super().__new__(cls, name, bases, dct)
        except TypeError:
            if added:   # The __weakref__ slot might be in a parent class
                dct["__slots__"].pop("__weakref__")
                cls = super().__new__(cls, name, bases, dct)
            else:
                raise
        # The list that will store all instances
        cls.__instances = s
        return cls
    
    def __iter__(self : type[T]) -> Generator[T, None, None]:
        """
        Implements the iteration over the class' instances
        """
        yield from tuple(self.__instances)
    
    def __len__(self) -> int:
        """
        Implements the len of this class (the number of existing instances)
        """
        return len(self.__instances)




class InstanceReferencingHierarchy(type):

    """
    Creates an InstanceReferencingClass group. In such a group, iterating a class will also allow you to iterate over the subclasses.

    Just instanciate it to create a new metaclass:

    >>> class A(metaclass = InstanceReferencingHierarchy):
    ...     pass
    ... class B(A):
    ...     pass
    ... class C(metaclass = InstanceReferencingHierarchy):
    ...     pass
    ...
    >>> a1 = A()
    >>> a2 = A()
    >>> b = B()
    >>> c = C()
    >>> list(A)
    [<__main__.B object at 0x000001C607E30A00>, <__main__.A object at 0x000001C607E309A0>, <__main__.A object at 0x000001C607E309D0>]
    >>> list(B)
    [<__main__.B object at 0x000001C607E30A00>]
    >>> list(C)
    [<__main__.C object at 0x000001C607E30EE0>]
    >>> del b
    >>> list(A)
    [<__main__.A object at 0x000001C607E309A0>, <__main__.A object at 0x000001C607E309D0>]
    """

    __instances : dict[type, WeakValueDictionary[int, Any]] = {}

    def __new__(cls, name : str, bases : tuple[type], dct : dict):
        """
        Implements the creation of a new class
        """            
        from weakref import WeakValueDictionary
        from .utils import signature_def, signature_call
        from functools import wraps

        s = WeakValueDictionary()

        def extract_slots(o : type) -> set[str]:
            if not hasattr(o, "__slots__"):
                s = set()
            else:
                s = set(o.__slots__)
            return s.union(*[extract_slots(b) for b in o.__bases__])

        added = False
        # if this class has __slots__, then a __weakref__ slot is necessary
        if "__slots__" in dct and "__weakref__" not in dct["__slots__"] and not any("__weakref__" in extract_slots(b) for b in bases):
            added = True
            if isinstance(dct["__slots__"], dict):
                dct["__slots__"]["__weakref__"] = "The slot for the weakref of this object"
            elif isinstance(cls, (Sequence)):
                dct["__slots__"] = list(dct["__slots__"]) + ["__weakref__"]
        
        # Finding the __new__ method 
        old_new = None
        if "__new__" in dct:
            old_new = dct["__new__"]
        else:
            for b in bases:
                if hasattr(b, "__new__"):
                    old_new = getattr(b, "__new__")
        if old_new == None:
            old_new = object.__new__
        
        sig = "@wraps(old_target)\n"

        sig_def, env = signature_def(old_new, init_env = {"old_target" : old_new, "wraps" : wraps, "cls_dict" : s})
        
        code = sig + sig_def

        if old_new == object.__new__:       # Because object.__new__ says it would accept additional args passed to __init__, but in reality, it doesn't...
            code += "\n\tres = old_target(args[0])"
        else:
            code += "\n\tres = old_target(" + signature_call(old_new, decorate=False) + ")"

        code += "\n\tfrom builtins import id"

        code += "\n\tcls_dict[id(res)] = res"

        code += "\n\treturn res"

        exec(code, env)

        dct["__new__"] = env[old_new.__name__]

        # Creating the class
        try:
            cls = super().__new__(cls, name, bases, dct)
        except TypeError:
            if added:   # The __weakref__ slot might be in a parent class
                dct["__slots__"].pop("__weakref__")
                cls = super().__new__(cls, name, bases, dct)
            else:
                raise
        # The Weakdict that will store all instances
        InstanceReferencingHierarchy.__instances[cls] = s
        return cls

    def __iter__(self : type[T]) -> Generator[T, None, None]:
        """
        Implements the iteration over the class' instances
        """
        for cls, cls_set in tuple(InstanceReferencingHierarchy.__instances.items()):
            if issubclass(cls, self):
                yield from cls_set.values()
    
    def __len__(self) -> int:
        """
        Implements the len of this class (the number of existing instances)
        """
        l = 0
        for cls, cls_set in tuple(InstanceReferencingHierarchy.__instances.items()):
            if issubclass(cls, self):
                l += len(cls_set)
        return l





class InstancePreservingHierarchy(type):

    """
    Creates an InstanceReferencingClass group. In such a group, iterating a class will also allow you to iterate over the subclasses.

    Just instanciate it to create a new metaclass:

    >>> class A(metaclass = InstancePreservingHierarchy):
    ...     pass
    ... class B(A):
    ...     pass
    ... class C(metaclass = InstancePreservingHierarchy):
    ...     pass
    ...
    >>> a1 = A()
    >>> a2 = A()
    >>> b = B()
    >>> c = C()
    >>> list(A)
    [<__main__.B object at 0x000001C607E30A00>, <__main__.A object at 0x000001C607E309A0>, <__main__.A object at 0x000001C607E309D0>]
    >>> list(B)
    [<__main__.B object at 0x000001C607E30A00>]
    >>> list(C)
    [<__main__.C object at 0x000001C607E30EE0>]
    >>> del b
    >>> list(A)
    [<__main__.B object at 0x000001C607E30A00>, <__main__.A object at 0x000001C607E309A0>, <__main__.A object at 0x000001C607E309D0>]
    """

    __instances : dict[type, list] = {}

    def __new__(cls, name : str, bases : tuple[type], dct : dict):
        """
        Implements the creation of a new class
        """
        from .utils import signature_def, signature_call
        from functools import wraps

        s = []

        def extract_slots(o : type) -> set[str]:
            if not hasattr(o, "__slots__"):
                s = set()
            else:
                s = set(o.__slots__)
            return s.union(*[extract_slots(b) for b in o.__bases__])

        added = False

        # Finding the __new__ method 
        old_new = None
        if "__new__" in dct:
            old_new = dct["__new__"]
        else:
            for b in bases:
                if hasattr(b, "__new__"):
                    old_new = getattr(b, "__new__")
        if old_new == None:
            old_new = object.__new__
        
        sig = "@wraps(old_target)\n"

        sig_def, env = signature_def(old_new, init_env = {"old_target" : old_new, "wraps" : wraps, "cls_list" : s})
        
        code = sig + sig_def

        if old_new == object.__new__:       # Because object.__new__ says it would accept additional args passed to __init__, but in reality, it doesn't...
            code += "\n\tres = old_target(args[0])"
        else:
            code += "\n\tres = old_target(" + signature_call(old_new, decorate=False) + ")"

        code += "\n\tcls_list.append(res)"

        code += "\n\treturn res"

        exec(code, env)

        dct["__new__"] = env[old_new.__name__]

        # if this class has __slots__, then a __weakref__ slot is necessary
        if "__slots__" in dct and "__weakref__" not in dct["__slots__"] and not any("__weakref__" in extract_slots(b) for b in bases):
            added = True
            if isinstance(dct["__slots__"], dict):
                dct["__slots__"]["__weakref__"] = "The slot for the weakref of this object"
            elif isinstance(cls, (Sequence)):
                dct["__slots__"] = list(dct["__slots__"]) + ["__weakref__"]
        # Creating the class
        try:
            cls = super().__new__(cls, name, bases, dct)
        except TypeError:
            if added:   # The __weakref__ slot might be in a parent class
                dct["__slots__"].pop("__weakref__")
                cls = super().__new__(cls, name, bases, dct)
            else:
                raise
        # The list that will store all instances
        InstancePreservingHierarchy.__instances[cls] = s
        return cls
    
    def __iter__(self : type[T]) -> Generator[T, None, None]:
        """
        Implements the iteration over the class' instances
        """
        for cls, cls_set in tuple(InstancePreservingHierarchy.__instances.items()):
            if issubclass(cls, self):
                yield from cls_set
    
    def __len__(self) -> int:
        """
        Implements the len of this class (the number of existing instances)
        """
        l = 0
        for cls, cls_set in tuple(InstancePreservingHierarchy.__instances.items()):
            if issubclass(cls, self):
                l += len(cls_set)
        return l



    

del T, Any, Generator, Sequence, TypeVar, WeakValueDictionary