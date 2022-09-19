"""
This module adds metaclasses that make classes iterable, yielding all of their instances.
"""


from typing import Any, Iterator, Sequence, TypeVar
from weakref import WeakSet

__all__ = ["InstanceReferencingClass", "InstancePreservingClass", "InstanceReferencingHierarchy", "InstancePreservingHierarchy"]





CLS = TypeVar("CLS")

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

    def __new__(cls : type[CLS], name : str, bases : tuple[type], dct : dict):
        """
        Implements the creation of a new class
        """
        from weakref import WeakSet
        from typing import Set
        
        def extract_slots(o : type) -> Set[str]:
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
        # Creating the class
        try:
            cls = super().__new__(cls, name, bases, dct)
        except TypeError:
            if added:   # The __weakref__ slot might be in a parent class
                dct["__slots__"].pop("__weakref__")
                cls = super().__new__(cls, name, bases, dct)
            else:
                raise
        # The WeakSet that will store all instances
        cls.__instances = WeakSet()
        return cls

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """
        Implements creation of a class instance.
        """
        ist = super().__call__(*args, **kwargs)
        # Add the created instance to the WeakSet
        self.__instances.add(ist)
        return ist
    
    def __iter__(self) -> Iterator[CLS]:
        """
        Implements the iteration over the class' instances
        """
        # A copy of the WeakSet is necessary (in case of creation or deletion)
        return iter(set(self.__instances))
    
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

    def __new__(cls : type[CLS], name : str, bases : tuple[type], dct : dict):
        """
        Implements the creation of a new class
        """
        from typing import Set
        
        def extract_slots(o : type) -> Set[str]:
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
        # Creating the class
        try:
            cls = super().__new__(cls, name, bases, dct)
        except TypeError:
            if added:   # The __weakref__ slot might be in a parent class
                dct["__slots__"].pop("__weakref__")
                cls = super().__new__(cls, name, bases, dct)
            else:
                raise
        # The WeakSet that will store all instances
        cls.__instances = set()
        return cls
    
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """
        Implements creation of a class instance.
        """
        ist = super().__call__(*args, **kwargs)
        # Add the created instance to the WeakSet
        self.__instances.add(ist)
        return ist
    
    def __iter__(self) -> Iterator[CLS]:
        """
        Implements the iteration over the class' instances
        """
        # A copy of the WeakSet is necessary (in case of creation or deletion)
        return iter(self.__instances.copy())
    
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

    __instances : dict[type[CLS], WeakSet[CLS]] = {}

    def __new__(cls : type[CLS], name : str, bases : tuple[type], dct : dict):
        """
        Implements the creation of a new class
        """            
        from weakref import WeakSet
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
        # Creating the class
        try:
            cls = super().__new__(cls, name, bases, dct)
        except TypeError:
            if added:   # The __weakref__ slot might be in a parent class
                dct["__slots__"].pop("__weakref__")
                cls = super().__new__(cls, name, bases, dct)
            else:
                raise
        InstanceReferencingHierarchy.__instances[cls] = WeakSet()
        return cls

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """
        Implements creation of a class instance.
        """
        ist = super().__call__(*args, **kwargs)
        # Add the created instance to the WeakSet
        InstanceReferencingHierarchy.__instances[self].add(ist)
        return ist
    
    def __iter__(self) -> Iterator[CLS]:
        """
        Implements the iteration over the class' instances
        """
        # A copy of the WeakSet is necessary (in case of creation or deletion)
        s = set()
        for cls, cls_set in InstanceReferencingHierarchy.__instances.items():
            if issubclass(cls, self):
                s.update(cls_set)
        return iter(s)
    
    def __len__(self) -> int:
        """
        Implements the len of this class (the number of existing instances)
        """
        l = 0
        for cls, cls_set in InstanceReferencingHierarchy.__instances.items():
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

    __instances : dict[type[CLS], set[CLS]] = {}

    def __new__(cls : type[CLS], name : str, bases : tuple[type], dct : dict):
        """
        Implements the creation of a new class
        """
        from typing import Set
        
        def extract_slots(o : type) -> Set[str]:
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
        # Creating the class
        try:
            cls = super().__new__(cls, name, bases, dct)
        except TypeError:
            if added:   # The __weakref__ slot might be in a parent class
                dct["__slots__"].pop("__weakref__")
                cls = super().__new__(cls, name, bases, dct)
            else:
                raise
        # The WeakSet that will store all instances
        InstancePreservingHierarchy.__instances[cls] = set()
        return cls
    
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """
        Implements creation of a class instance.
        """
        ist = super().__call__(*args, **kwargs)
        # Add the created instance to the WeakSet
        InstancePreservingHierarchy.__instances[self].add(ist)
        return ist
    
    def __iter__(self) -> Iterator[CLS]:
        """
        Implements the iteration over the class' instances
        """
        # A copy of the WeakSet is necessary (in case of creation or deletion)
        s = set()
        for cls, cls_set in InstancePreservingHierarchy.__instances.items():
            if issubclass(cls, self):
                s.update(cls_set)
        return iter(s)
    
    def __len__(self) -> int:
        """
        Implements the len of this class (the number of existing instances)
        """
        l = 0
        for cls, cls_set in InstancePreservingHierarchy.__instances.items():
            if issubclass(cls, self):
                l += len(cls_set)
        return l



    

del Any, Iterator, Sequence, TypeVar, CLS, WeakSet