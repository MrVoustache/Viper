"""
This module defines collections which are like sets and dict but they allow for repetition and have advance lookup methods.
"""

from collections.abc import ItemsView, MutableSet, KeysView, MutableMapping, ValuesView
from typing import AbstractSet, Any, Generic, Iterable, Iterator, Mapping, TypeVar, Hashable, overload

__all__ = ["IsoSet", "IsoDict"]





K = TypeVar("K", bound=Hashable)

class IsoSet(MutableSet[K]):

    """
    The isomorphic set is a container similar to set except that it can contain equal objects that are not the same objects in memory (a is not b but a == b), differenciate them, but still search for them.
    Can also be called a multi-set.
    """

    from typing import AbstractSet as __AbstractSet, Iterable as __Iterable, Hashable as __Hashable
    from sys import getsizeof
    __getsizeof = staticmethod(getsizeof)
    del getsizeof

    __slots__ = {
        "__table" : "The association table used to store all the elements of the IsoSet.",
        "__len" : "The size of the IsoSet."
    }

    def __init__(self, iterable : Iterable[K] = ()) -> None:
        if not isinstance(iterable, IsoSet.__Iterable):
            raise TypeError(f"Expected iterable, got '{type(iterable).__name__}'")
        
        self.__table : "dict[int, dict[int, K]]" = {}
        for t in iterable:
            if not isinstance(t, IsoSet.__Hashable):
                raise TypeError(f"unhashable type: '{type(t).__name__}'")
            self.__table.setdefault(hash(t), {})[id(t)] = t
        self.__len = sum(len(hdict) for hdict in self.__table.values())
                
    def __repr__(self) -> str:
        return f"{type(self).__name__}([{', '.join(repr(e) for e in self)}])"
    
    def __str__(self) -> str:
        return "{" + ', '.join(str(e) for e in self) + "}"

    def __contains__(self, x) -> bool:
        """
        Implements x in self. Returns True if x is itself in self.
        """
        if not isinstance(x, IsoSet.__Hashable):
            raise TypeError(f"unhashable type: '{type(x).__name__}'")
        h = hash(x)
        return h in self.__table and id(x) in self.__table[h]
    
    def iso_contains(self, x : object) -> bool:
        """
        Like x in self, but also returns True if any object in self equals x.
        """
        if not isinstance(x, IsoSet.__Hashable):
            raise TypeError(f"unhashable type: '{type(x).__name__}'")
        h = hash(x)
        return h in self.__table and (id(x) in self.__table[h] or any(x == v for v in self.__table[h].values()))
    
    def __iter__(self) -> Iterator[K]:
        """
        Implements iter(self).
        """
        return (k for hvalues in self.__table.values() for k in hvalues.values())

    def __len__(self) -> int:
        """
        Implements len(self).
        """
        return self.__len
    
    def __bool__(self) -> bool:
        """
        Implements bool(self).
        """
        return self.__len > 0
    
    def add(self, value: K) -> None:
        if not isinstance(value, IsoSet.__Hashable):
            raise TypeError(f"unhashable type: '{type(value).__name__}'")
        if value in self:
            return
        self.__table.setdefault(hash(value), {})[id(value)] = value
        self.__len += 1

    def clear(self) -> None:
        self.__table.clear()
        self.__len = 0

    def copy(self) -> "IsoSet[K]":
        """
        Return a shallow copy of an IsoSet.
        """
        cp = IsoSet()
        cp.__table = {h : hdict.copy() for h, hdict in self.__table.items()}
        cp.__len = self.__len
        return cp
        
    def difference(self, *sets : AbstractSet[K]) -> "IsoSet[K]":
        """
        Return the difference of two or more sets as a new IsoSet.

        (i.e. all elements that are in this set but not the others.)
        """
        s = self.copy()
        for si in sets:
            if not isinstance(si, IsoSet.__Iterable):
                raise TypeError(f"Expected iterable, got '{type(si).__name__}'")
        for si in sets:
            s -= si
        return s
    
    def difference_update(self, *sets : AbstractSet[K]):
        """
        Remove all elements of another set from this IsoSet.
        """
        for si in sets:
            if not isinstance(si, IsoSet.__Iterable):
                raise TypeError(f"Expected iterable, got '{type(si).__name__}'")
        for si in sets:
            self -= si
    
    def discard(self, value: K) -> None:
        if not isinstance(value, IsoSet.__Hashable):
            raise TypeError(f"unhashable type: '{type(value).__name__}'")
        if value not in self:
            return
        h = hash(value)
        hdict = self.__table[h]
        hdict.pop(id(value))
        self.__len -= 1
        if not hdict:
            self.__table.pop(h)

    def intersection(self, *sets : AbstractSet[K]) -> "IsoSet[K]":
        """
        Return the difference of two or more sets as a new IsoSet.

        (i.e. all elements that are in this set but not the others.)
        """
        s = self.copy()
        for si in sets:
            if not isinstance(si, IsoSet.__Iterable):
                raise TypeError(f"Expected iterable, got '{type(si).__name__}'")
        for si in sets:
            s &= si
        return s
    
    def intersection_update(self, *sets : AbstractSet[K]):
        """
        Update an IsoSet with the intersection of itself and another.
        """
        for si in sets:
            if not isinstance(si, IsoSet.__Iterable):
                raise TypeError(f"Expected iterable, got '{type(si).__name__}'")
        for si in sets:
            self &= si
    
    def isdisjoint(self, s : AbstractSet[K]) -> bool:
        """
        Return True if two sets have a null intersection.
        """
        if not isinstance(s, IsoSet.__Iterable):
            raise TypeError(f"Expected iterable, got '{type(s).__name__}'")
        return bool(self & s)
    
    def issubset(self, s : AbstractSet[K]) -> bool:
        """
        Report whether another set contains this IsoSet.
        """
        if not isinstance(s, IsoSet.__Iterable):
            raise TypeError(f"Expected iterable, got '{type(s).__name__}'")
        return self <= s
    
    def issuperset(self, s : AbstractSet[K]) -> bool:
        """
        Report whether this IsoSet contains another set.
        """
        if not isinstance(s, IsoSet.__Iterable):
            raise TypeError(f"Expected iterable, got '{type(s).__name__}'")
        return self >= s
    
    def pop(self) -> K:
        """
        Remove and return an arbitrary IsoSet element.
        Raises KeyError if the IsoSet is empty.
        """
        if not self:
            raise KeyError("'pop from empty IsoSet'")
        h, hdict = self.__table.popitem()
        i, e = hdict.popitem()
        if hdict:
            self.__table[h] = hdict
        return e
        
    def remove(self, e : K):
        """
        Remove an element from an IsoSet; it must be a member.

        If the element is not a member, raise a KeyError.
        """
        if e in self:
            self.discard(e)
        else:
            raise KeyError(repr(e))
    
    def symmetric_difference(self, s : AbstractSet[K]) -> "IsoSet[K]":
        """
        Return the symmetric difference of two sets as a new set.

        (i.e. all elements that are in exactly one of the sets.)
        """
        if not isinstance(s, IsoSet.__Iterable):
            raise TypeError(f"Expected iterable, got '{type(s).__name__}'")
        res = self ^ s
        if not isinstance(res, IsoSet):
            res = IsoSet(res)
        return res
    
    def symmetric_difference_update(self, s : AbstractSet[K]):
        """
        Update an IsoSet with the symmetric difference of itself and another.
        """
        if not isinstance(s, IsoSet.__Iterable):
            raise TypeError(f"Expected iterable, got '{type(s).__name__}'")
        self ^= s

    def union(self, *sets : AbstractSet[K]) -> "IsoSet[K]":
        """
        Return the union of sets as a new set.

        (i.e. all elements that are in either set.)
        """
        s = self.copy()
        for si in sets:
            if not isinstance(si, IsoSet.__Iterable):
                raise TypeError(f"Expected iterable, got '{type(si).__name__}'")
        for si in sets:
            s |= si
        return s
    
    def update(self, *sets : AbstractSet[K]):
        """
        Update an IsoSet with the union of itself and others.
        """
        for si in sets:
            if not isinstance(si, IsoSet.__Iterable):
                raise TypeError(f"Expected iterable, got '{type(si).__name__}'")
        for si in sets:
            self |= si
    
    def __sizeof__(self) -> int:
        return super().__sizeof__() + IsoSet.__getsizeof(self.__table) + sum(IsoSet.__getsizeof(hdict) for hdict in self.__table.values())
    
    def __getstate__(self) -> object:
        return {
            "__table" : self.__table,
            "__len" : self.__len,
            }
    
    def __eq__(self, value: object) -> bool:
        if not isinstance(value, IsoSet.__AbstractSet):
            return False
        return len(self) == len(value) and all(e in value for e in self)
    
    def __le__(self, other: AbstractSet[Any]) -> bool:
        if self is other:
            return True
        if not isinstance(other, IsoSet.__AbstractSet):
            raise TypeError(f"'<=' not supported between instances of '{type(self).__name__}' and '{type(other).__name__}'")
        if not isinstance(other, IsoSet):
            return len(self) <= len(other) and all(k in other for k in self)
        return (self.__table.keys() <= other.__table.keys()) and all(self.__table[h].keys() <= other.__table[h].keys() for h in self.__table.keys())
    
    def __lt__(self, other: AbstractSet[Any]) -> bool:
        if self is other:
            return False
        if not isinstance(other, IsoSet.__AbstractSet):
            raise TypeError(f"'<' not supported between instances of '{type(self).__name__}' and '{type(other).__name__}'")
        if not isinstance(other, IsoSet):
            return len(self) < len(other) and all(k in other for k in self)
        return self <= other and len(self) != len(other)
    
    def __ge__(self, other: AbstractSet[Any]) -> bool:
        if self is other:
            return True
        if not isinstance(other, IsoSet.__AbstractSet):
            raise TypeError(f"'>=' not supported between instances of '{type(self).__name__}' and '{type(other).__name__}'")
        if not isinstance(other, IsoSet):
            return len(self) >= len(other) and all(k in self for k in other)
        return (self.__table.keys() >= other.__table.keys()) and all(self.__table[h].keys() >= other.__table[h].keys() for h in other.__table.keys())
    
    def __gt__(self, other: AbstractSet[Any]) -> bool:
        if self is other:
            return False
        if not isinstance(other, IsoSet.__AbstractSet):
            raise TypeError(f"'>' not supported between instances of '{type(self).__name__}' and '{type(other).__name__}'")
        if not isinstance(other, IsoSet):
            return len(self) >= len(other) and all(k in self for k in other)
        return self >= other and len(self) != len(other)
    
    def __and__(self, other : AbstractSet[K]) -> "IsoSet[K]":
        if not isinstance(other, IsoSet.__AbstractSet):
            return NotImplemented
        if len(self) > len(other):
            return IsoSet(k for k in other if k in self)
        else:
            return IsoSet(k for k in self if k in other)
    
    def __rand__(self, other : AbstractSet[K]) -> "IsoSet[K]":
        if not isinstance(other, IsoSet.__AbstractSet):
            return NotImplemented
        if len(self) > len(other):
            return IsoSet(k for k in other if k in self)
        else:
            return IsoSet(k for k in self if k in other)
        
    def __iand__(self, other : AbstractSet[K]) -> "IsoSet[K]":
        if not isinstance(other, IsoSet.__AbstractSet):
            return NotImplemented
        for k in self.copy():
            if k not in other:
                self.remove(k)
        return self
    
    def __or__(self, other : AbstractSet[K]) -> "IsoSet[K]":
        if not isinstance(other, IsoSet.__AbstractSet):
            return NotImplemented
        s = IsoSet(self)
        for k in other:
            s.add(k)
        return s
    
    def __ror__(self, other : AbstractSet[K]) -> "IsoSet[K]":
        if not isinstance(other, IsoSet.__AbstractSet):
            return NotImplemented
        s = IsoSet(self)
        for k in other:
            s.add(k)
        return s
    
    def __ior__(self, other : AbstractSet[K]) -> "IsoSet[K]":
        if not isinstance(other, IsoSet.__AbstractSet):
            return NotImplemented
        for k in other:
            self.add(k)
        return self
    
    def __sub__(self, other : AbstractSet[K]) -> "IsoSet[K]":
        if not isinstance(other, IsoSet.__AbstractSet):
            return NotImplemented
        return IsoSet(k for k in self if k not in other)
    
    def __rsub__(self, other : AbstractSet[K]) -> "IsoSet[K]":
        if not isinstance(other, IsoSet.__AbstractSet):
            return NotImplemented
        return IsoSet(k for k in other if k not in self)
    
    def __isub__(self, other : AbstractSet[K]) -> "IsoSet[K]":
        if not isinstance(other, IsoSet.__AbstractSet):
            return NotImplemented
        for k in other:
            self.discard(k)
        return self
    
    def __xor__(self, other : AbstractSet[K]) -> "IsoSet[K]":
        if not isinstance(other, IsoSet.__AbstractSet):
            return NotImplemented
        s = IsoSet()
        for k in self:
            if k not in other:
                s.add(k)
        for k in other:
            if k not in self:
                s.add(k)
        return s
    
    def __rxor__(self, other : AbstractSet[K]) -> "IsoSet[K]":
        if not isinstance(other, IsoSet.__AbstractSet):
            return NotImplemented
        s = IsoSet()
        for k in self:
            if k not in other:
                s.add(k)
        for k in other:
            if k not in self:
                s.add(k)
        return s
    
    def __ixor__(self, other : AbstractSet[K]) -> "IsoSet[K]":
        if not isinstance(other, IsoSet.__AbstractSet):
            return NotImplemented
        for k in other:
            if k in self:
                self.remove(k)
            else:
                self.add(k)
        return self





V = TypeVar("V")

class IsoDictKeys(KeysView[K], Generic[K, V]):

    """
    This is the equivalent class of dict_keys that list keys of IsoDicts.
    """

    from typing import AbstractSet as __AbstractSet, Hashable as __Hashable

    __slots__ = {
        "__mapping" : "The mapping that this view refers to.",
        "__table" : "The association table used to store all the elements of the isoset."
    }

    def __init__(self, mapping: "IsoDict[K, V]") -> None:
        if not isinstance(mapping, IsoDict):
            raise TypeError(f"Expected IsoDict, got '{type(mapping).__name__}'")
        self.__mapping = mapping
        self.__table : "dict[int, dict[int, tuple[K, V]]]" = mapping._IsoDict__table # type: ignore

    @property
    def mapping(self) -> "IsoDict[K, V]":
        """
        The mapping this view refers to.
        """
        return self.__mapping

    def __repr__(self) -> str:
        return f"{type(self).__name__}([{', '.join(str(k) for k in self)}])"
    
    def __contains__(self, k: object) -> bool:
        """
        Implements k in self. Contrary to IsoDict, this will return True if an object equal to k is in self.
        """
        if not isinstance(k, IsoDictKeys.__Hashable):
            raise TypeError(f"unhashable type: '{type(k).__name__}'")
        h = hash(k)
        return h in self.__table and (id(k) in self.__table[h] or any(k == ki for ki, vi in self.__table[h].values()))
    
    def __eq__(self, value: object) -> bool:
        if not isinstance(value, IsoDictKeys.__AbstractSet):
            return False
        return len(self) == len(value) and all(k in value for k in self)
    
    def __le__(self, other: AbstractSet[Any]) -> bool:
        if self is other:
            return True
        if not isinstance(other, IsoDictKeys.__AbstractSet):
            raise TypeError(f"'<=' not supported between instances of '{type(self).__name__}' and '{type(other).__name__}'")
        if not isinstance(other, IsoDictKeys):
            return len(self) <= len(other) and all(k in other for k in self)
        return (self.__table.keys() <= other.__table.keys()) and all(self.__table[h].keys() <= other.__table[h].keys() for h in self.__table.keys())
    
    def __lt__(self, other: AbstractSet[Any]) -> bool:
        if self is other:
            return False
        if not isinstance(other, IsoDictKeys.__AbstractSet):
            raise TypeError(f"'<' not supported between instances of '{type(self).__name__}' and '{type(other).__name__}'")
        if not isinstance(other, IsoDictKeys):
            return len(self) < len(other) and all(k in other for k in self)
        return self <= other and len(self) != len(other)
    
    def __ge__(self, other: AbstractSet[Any]) -> bool:
        if self is other:
            return True
        if not isinstance(other, IsoDictKeys.__AbstractSet):
            raise TypeError(f"'>=' not supported between instances of '{type(self).__name__}' and '{type(other).__name__}'")
        if not isinstance(other, IsoDictKeys):
            return len(self) >= len(other) and all(k in self for k in other)
        return (self.__table.keys() >= other.__table.keys()) and all(self.__table[h].keys() >= other.__table[h].keys() for h in other.__table.keys())
    
    def __gt__(self, other: AbstractSet[Any]) -> bool:
        if self is other:
            return False
        if not isinstance(other, IsoDictKeys.__AbstractSet):
            raise TypeError(f"'>' not supported between instances of '{type(self).__name__}' and '{type(other).__name__}'")
        if not isinstance(other, IsoDictKeys):
            return len(self) >= len(other) and all(k in self for k in other)
        return self >= other and len(self) != len(other)
    
    def __iter__(self) -> Iterator[K]:
        return (k for hvalues in self.__table.values() for k, v in hvalues.values())
    
    def __reversed__(self) -> Iterator[K]:
        return (k for hvalues in reversed(self.__table.values()) for k, v in reversed(hvalues.values()))
    
    def __len__(self) -> int:
        return len(self.__mapping)
    
    def isdisjoint(self, other: Iterable[Any]) -> bool:
        return all(k not in self for k in other)
    
    def __and__(self, other: Iterable[K]) -> IsoSet[K]:
        return IsoSet(self) & IsoSet(other)
    
    def __rand__(self, other: Iterable[K]) -> IsoSet[K]:
        return IsoSet(other) & IsoSet(self)

    def __or__(self, other: Iterable[K]) -> IsoSet[K]:
        return IsoSet(self) | IsoSet(other)
    
    def __ror__(self, other: Iterable[K]) -> IsoSet[K]:
        return IsoSet(other) | IsoSet(self)
    
    def __sub__(self, other: Iterable[K]) -> IsoSet[K]:
        return IsoSet(self) - IsoSet(other)
    
    def __rsub__(self, other: Iterable[K]) -> IsoSet[K]:
        return IsoSet(other) | IsoSet(self)
    
    def __xor__(self, other: Iterable[K]) -> IsoSet[K]:
        return IsoSet(self) ^ IsoSet(other)
    
    def __rxor__(self, other: Iterable[K]) -> IsoSet[K]:
        return IsoSet(other) ^ IsoSet(self)
    




class IsoDictValues(ValuesView[V], Generic[K, V]):

    """
    This is the equivalent class of dict_values that list values of IsoDicts.
    """

    from typing import ValuesView as __ValuesView

    __slots__ = {
        "__mapping" : "The mapping that this view refers to.",
        "__table" : "The association table used to store all the elements of the IsoDict."
    }

    def __init__(self, mapping: "IsoDict[K, V]") -> None:
        if not isinstance(mapping, IsoDict):
            raise TypeError(f"Expected IsoDict, got '{type(mapping).__name__}'")
        self.__mapping = mapping
        self.__table : "dict[int, dict[int, tuple[K, V]]]" = mapping._IsoDict__table # type: ignore

    @property
    def mapping(self) -> "IsoDict[K, V]":
        """
        The mapping this view refers to.
        """
        return self.__mapping

    def __repr__(self) -> str:
        return f"{type(self).__name__}([{', '.join(str(v) for v in self)}])"
    
    def __iter__(self) -> Iterator[V]:
        return (v for hvalues in self.__table.values() for k, v in hvalues.values())
    
    def __reversed__(self) -> Iterator[V]:
        return (v for hvalues in reversed(self.__table.values()) for k, v in reversed(hvalues.values()))
    
    def __len__(self) -> int:
        return len(self.__mapping)
    
    def __eq__(self, value: object) -> bool:
        return isinstance(value, IsoDictValues.__ValuesView) and len(self) == len(value) and all(a == b for a, b in zip(self, value))





class IsoDictItems(ItemsView[K, V]):

    """
    This is the equivalent class of dict_items that list items of IsoDicts.
    """

    from typing import AbstractSet as __AbstractSet, Hashable as __Hashable

    __slots__ = {
        "__mapping" : "The mapping that this view refers to.",
        "__table" : "The association table used to store all the elements of the IsoDict."
    }

    def __init__(self, mapping: "IsoDict[K, V]") -> None:
        if not isinstance(mapping, IsoDict):
            raise TypeError(f"Expected IsoDict, got '{type(mapping).__name__}'")
        self.__mapping = mapping
        self.__table : "dict[int, dict[int, tuple[K, V]]]" = mapping._IsoDict__table # type: ignore

    @property
    def mapping(self) -> "IsoDict[K, V]":
        """
        The mapping this view refers to.
        """
        return self.__mapping
    
    def __repr__(self) -> str:
        return f"{type(self).__name__}([{', '.join(str(t) for t in self)}])"
    
    def __iter__(self) -> Iterator[tuple[K, V]]:
        return ((k, v) for hvalues in self.__table.values() for k, v in hvalues.values())
    
    def __reversed__(self) -> Iterator[tuple[K, V]]:
        return ((k, v) for hvalues in reversed(self.__table.values()) for k, v in reversed(hvalues.values()))
    
    def __len__(self) -> int:
        return len(self.__mapping)
    
    def __contains__(self, item: object) -> bool:
        if not isinstance(item, tuple) or len(item) != 2:
            return False
        k, v = item
        if not isinstance(k, IsoDictItems.__Hashable):
            return False
        return k in self.__mapping and self.__mapping[k] == v
    
    def __eq__(self, value: object) -> bool:
        if not isinstance(value, IsoDictItems.__AbstractSet):
            return False
        return len(self) == len(value) and all(k in value for k in self)
    
    def isdisjoint(self, other: Iterable[Any]) -> bool:
        return all(k not in self for k in other)
    
    def __and__(self, other: Iterable[tuple[K, V]]) -> IsoSet[tuple[K, V]]:
        return IsoSet(self) & IsoSet(other)
    
    def __rand__(self, other: Iterable[tuple[K, V]]) -> IsoSet[tuple[K, V]]:
        return IsoSet(other) & IsoSet(self)

    def __or__(self, other: Iterable[tuple[K, V]]) -> IsoSet[tuple[K, V]]:
        return IsoSet(self) | IsoSet(other)
    
    def __ror__(self, other: Iterable[tuple[K, V]]) -> IsoSet[tuple[K, V]]:
        return IsoSet(other) | IsoSet(self)
    
    def __sub__(self, other: Iterable[tuple[K, V]]) -> IsoSet[tuple[K, V]]:
        return IsoSet(self) - IsoSet(other)
    
    def __rsub__(self, other: Iterable[tuple[K, V]]) -> IsoSet[tuple[K, V]]:
        return IsoSet(other) | IsoSet(self)
    
    def __xor__(self, other: Iterable[tuple[K, V]]) -> IsoSet[tuple[K, V]]:
        return IsoSet(self) ^ IsoSet(other)
    
    def __rxor__(self, other: Iterable[tuple[K, V]]) -> IsoSet[tuple[K, V]]:
        return IsoSet(other) ^ IsoSet(self)





class IsoDict(MutableMapping[K, V]):

    """
    The isomorphic dict is a container similar to dict except that it can contain keys that can be equal as long as they are not the same objects in memory (a is not b but a == b), differenciate them, but still search for them.
    Can also be called a multi-dict.
    """

    from typing import Iterable as __Iterable, Hashable as __Hashable, Mapping as __Mapping
    from sys import getsizeof
    __getsizeof = staticmethod(getsizeof)
    del getsizeof

    __slots__ = {
        "__table" : "The association table used to store all the elements of the IsoDict.",
        "__len" : "The size of the IsoDict."
    }

    @overload
    def __init__(self) -> None:
        ...

    @overload
    def __init__(self: "IsoDict[str, V]", **kwargs: V) -> None:
        ...

    @overload
    def __init__(self, iterable: Mapping[K, V]) -> None:
        ...

    @overload
    def __init__(self: "IsoDict[str, V]", iterable: Mapping[str, V], **kwargs: V) -> None:
        ...

    @overload
    def __init__(self, iterable: Iterable[tuple[K, V]]) -> None:
        ...

    @overload
    def __init__(self: "IsoDict[str, V]", iterable: Iterable[tuple[str, V]], **kwargs: V) -> None:
        ...

    def __init__(self, iterable = (), **kwargs) -> None:
        if not isinstance(iterable, IsoDict.__Iterable):
            raise TypeError(f"Expected iterable, got '{type(iterable)}'")
        if isinstance(iterable, IsoDict.__Mapping):
            iterable = iterable.items()
        
        self.__table : "dict[int, dict[int, tuple[K, V]]]" = {}
        try:
            for k, v in iterable:
                if not isinstance(k, IsoDict.__Hashable):
                    raise TypeError(f"unhashable type: '{type(k).__name__}'")
                self.__table.setdefault(hash(k), {})[id(k)] = (k, v) # type: ignore
        except ValueError:
            raise ValueError(f"Expected mapping or iterable of tuples of two elements, got '{type(iterable).__name__}'")
        for k, v in kwargs:
            self.__table.setdefault(hash(k), {})[id(k)] = (k, v) # type: ignore
        self.__len = sum(len(hdict) for hdict in self.__table.values())

    @overload
    @classmethod
    def fromkeys(cls, iterable : Iterable[K], value : V) -> "IsoDict[K, V]":
        ...

    @overload
    @classmethod
    def fromkeys(cls, iterable : Iterable[K], value : None = None) -> "IsoDict[K, None]":
        ...
    
    @classmethod
    def fromkeys(cls, iterable, value = None):
        return cls(((k, value) for k in iterable))

    def __repr__(self) -> str:
        return f"{type(self).__name__}([{', '.join(repr((k, v)) for k, v in self.items())}])"

    def __str__(self) -> str:
        return "{" + ', '.join(f"{k}: {v}" for k, v in self.items()) + "}"
    
    def __contains__(self, k: object) -> bool:
        """
        Implements k in self. Returns True if k itself is in self (using id()).
        """
        if not isinstance(k, IsoDict.__Hashable):
            raise TypeError(f"unhashable type: '{type(k).__name__}'")
        h = hash(k)
        return h in self.__table and id(k) in self.__table[h]
    
    def __iter__(self) -> Iterator[K]:
        """
        Implements iter(self).
        """
        return (k for hvalues in self.__table.values() for k, v in hvalues.values())
    
    def __reversed__(self) -> Iterator[K]:
        """
        Implements reversed(self).
        """
        return (k for hvalues in reversed(self.__table.values()) for k, v in reversed(hvalues.values()))
    
    def __len__(self) -> int:
        """
        Implements len(self).
        """
        return self.__len
    
    def __bool__(self) -> bool:
        """
        Implements bool(self).
        """
        return self.__len > 0
    
    def __getitem__(self, k: K) -> V:
        if not isinstance(k, IsoDict.__Hashable):
            raise TypeError(f"unhashable type: '{type(k).__name__}'")
        h = hash(k)
        if h in self.__table and id(k) in self.__table[h]:
            return self.__table[h][id(k)][1]
        raise KeyError(k)
    
    def __setitem__(self, k: K, v: V) -> None:
        if not isinstance(k, IsoDict.__Hashable):
            raise TypeError(f"unhashable type: '{type(k).__name__}'")
        h = hash(k)
        self.__table.setdefault(h, {})[id(k)] = (k, v)

    def __delitem__(self, k: K) -> None:
        if not isinstance(k, IsoDict.__Hashable):
            raise TypeError(f"unhashable type: '{type(k).__name__}'")
        h = hash(k)
        if h in self.__table and id(k) in self.__table[h]:
            hvalues = self.__table[h]
            hvalues.pop(id(k))
            if not hvalues:
                self.__table.pop(h)
        raise KeyError(k)
    
    def __getstate__(self):
        """
        Implements dumps(self).
        """
        return {
            "__table" : self.__table,
            "__len" : self.__len,
            }
    
    def clear(self) -> None:
        self.__table.clear()
        self.__len = 0

    def copy(self) -> "IsoDict[K, V]":
        """
        Return a shallow copy of an IsoDict.
        """
        cp = IsoDict()
        cp.__table = {h : hdict.copy() for h, hdict in self.__table.items()}
        cp.__len = self.__len
        return cp
    
    def pop(self, k : K) -> V:
        if not isinstance(k, IsoDict.__Hashable):
            raise TypeError(f"unhashable type: '{type(k).__name__}'")
        h = hash(k)
        if h in self.__table and id(k) in self.__table[h]:
            hvalues = self.__table[h]
            r = hvalues.pop(id(k))
            if not hvalues:
                self.__table.pop(h)
            return r[1]
        raise KeyError(k)
    
    def popitem(self) -> tuple[K, V]:
        """
        Remove and return an arbitrary IsoDict element.
        Raises KeyError if the IsoDict is empty.
        """
        if not self:
            raise KeyError("'popitem(): IsoDict is empty'")
        h, hdict = self.__table.popitem()
        i, e = hdict.popitem()
        if hdict:
            self.__table[h] = hdict
        return e
    
    def setdefault(self, k : K, default: V = None) -> V:
        if not isinstance(k, IsoDict.__Hashable):
            raise TypeError(f"unhashable type: '{type(k).__name__}'")
        h = hash(k)
        return self.__table.setdefault(h, {}).setdefault(id(k), (k, default))[1]
    
    def get(self, k : K, default : V = None) -> V:
        if not isinstance(k, IsoDict.__Hashable):
            raise TypeError(f"unhashable type: '{type(k).__name__}'")
        h = hash(k)
        if h in self.__table and id(k) in self.__table[h]:
            return self.__table[h][id(k)][1]
        return default
    
    @overload
    def update(self, iterable : Mapping[K, V] | Iterable[tuple[K, V]]):
        ...

    @overload
    def update(self : "IsoDict[str, V]", iterable : Mapping[str, V] | Iterable[tuple[str, V]], **kwargs : V):
        ...

    def update(self, iterable, **kwargs):
        if isinstance(iterable, IsoDict.__Mapping):
            iterable = iterable.items()
        try:
            for k, v in iterable:
                self[k] = v
        except ValueError:
            raise ValueError(f"Expected mapping or iterable of tuples of two elements, got '{type(iterable).__name__}'")
        for k, v in kwargs:
            self[k] = v
    
    def items(self) -> IsoDictItems[K, V]:
        return IsoDictItems(self)

    def keys(self) -> IsoDictKeys[K, V]:
        return IsoDictKeys(self)

    def values(self) -> IsoDictValues[K, V]:
        return IsoDictValues(self)

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, IsoDict.__Mapping):
            return False
        return len(self) == len(value) and all(k in value for k in self) and all(self[k] == value[k] for k in self)
    
    def __sizeof__(self) -> int:
        return super().__sizeof__() + IsoDict.__getsizeof(self.__table) + sum(IsoDict.__getsizeof(hdict) for hdict in self.__table.values())
    
    def __or__(self, other : Mapping[K, V]) -> "IsoDict[K, V]":
        if not isinstance(other, IsoDict.__Mapping):
            return NotImplemented
        s = self.copy()
        for k, v in other.items():
            s[k] = v
        return s
    
    def __ror__(self, other : Mapping[K, V]) -> "IsoDict[K, V]":
        if not isinstance(other, IsoDict.__Mapping):
            return NotImplemented
        s = IsoDict(other)
        for k, v in self.items():
            s[k] = v
        return s
    
    def __ior__(self, other : Mapping[K, V]) -> "IsoDict[K, V]":
        if not isinstance(other, IsoDict.__Mapping):
            return NotImplemented
        for k, v in other.items():
            self[k] = v
        return self
    




del K, V, ItemsView, MutableSet, KeysView, MutableMapping, ValuesView, AbstractSet, Any, Generic, Iterable, Iterator, Mapping, TypeVar, Hashable, overload