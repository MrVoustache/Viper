"""
This module adds frozendict, because dictionaries were jealous of sets!

Careful : This module actually gets erased by the frozendict class:
>>> from Viper import frozendict
>>> frozendict
<class 'Viper.frozendict.frozendict'>
"""


from typing import Any, Iterable, Mapping
from Viper.building.module_tools import clean_annotations, replace_module





class frozendict(dict):

    """
    A frozendict class. They are to dictionaries what frozensets are to sets.
    They are also hashable for example.
    To fill a frozendict, use the constructor (same as dict).
    """

    __slots__ = {
        "__hash" : "The hash of the frozendict"
    }

    def __delitem__(self, v):
        raise TypeError("'frozendict' object doesn't support item deletion")

    def __ior__(self, __value):
        return NotImplemented

    def __setitem__(self, k, v):
        raise TypeError("'frozendict' object does not support item assignment")

    def clear(self):
        raise AttributeError("'frozendict' object has no attribute 'clear'")

    def copy(self):
        return frozendict(super().copy())
    
    def pop(self, k):
        raise AttributeError("'frozendict' object has no attribute 'pop'")
    
    def popitem(self):
        raise AttributeError("'frozendict' object has no attribute 'popitem'")
    
    def setdefault(self, __key, __default):
        raise AttributeError("'frozendict' object has no attribute 'setdefault'")
    
    def update(self, iterable):
        raise AttributeError("'frozendict' object has no attribute 'update'")
    
    def __hash__(self) -> int:
        """
        Implements hash(self).
        """
        if not hasattr(self, "__hash"):
            self.__hash = 0
            for k, v in self.items():
                self.__hash += hash(k) * hash(v)
            self.__hash = hash(self.__hash)
        return self.__hash
    

    def __str__(self) -> str:
        return "frozendict(" + super().__str__() + ")"

    def __or__(self, __value: Mapping) -> "frozendict":
        return frozendict(super().__or__(__value))
    
    def __ror__(self, __value: Mapping) -> "frozendict":
        return frozendict(super().__ror__(__value))
    
    def fromkeys(iterable : Iterable, value : Any = None) -> "frozendict":
        return frozendict(super().fromkeys(iterable, value))


clean_annotations(frozendict)
replace_module("Viper.frozendict", frozendict)
del clean_annotations, replace_module, Any, Iterable, Mapping