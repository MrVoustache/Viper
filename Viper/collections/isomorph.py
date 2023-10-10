"""
This module defines collections which are like sets and dict but they allow for repetition and have advance lookup methods.

Note that to work, these collections assume that elements are not equal if their hashes are different and that equality is transitive.
"""

from collections.abc import ItemsView, MutableSet, KeysView, Mapping, MutableMapping, ValuesView, Set, Hashable, Iterable
from typing import Any, Generic, Iterator, TypeVar, overload

__all__ = ["IsoSet", "FrozenIsoSet", "IsoDict", "FrozenIsoDict"]





K = TypeVar("K", bound=Hashable)

class IsoSet(MutableSet[K]):

    """
    The isomorphic set is a container similar to set except that it can contain equal objects that are not the same objects in memory (a is not b but a == b):

    >>> a = 3714848721222
    >>> b = 3714848721222 + 1 - 1
    >>> a is b              # For large integers, CPython creates new objects for each result.
    False
    >>> IsoSet((3, 3, a, b))
    IsoSet([3, 3714848721222, 3714848721222])

    Note that for IsoSets, set operations are done in regards to object identity (with the id() function, for operators 'in', ==, !=, >, >=, <, <=).
    To switch between set comparison rules, use IsoSet.iso_view and IsoView.iso_set.
    """

    from collections.abc import Set as __Set, Iterable as __Iterable, Hashable as __Hashable
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
    
    def __getstate__(self):
        return {"data" : list(self)}

    def __setstate__(self, state):
        self.__table : "dict[int, dict[int, K]]" = {}
        for t in state["data"]:
            self.__table.setdefault(hash(t), {})[id(t)] = t # type: ignore
        self.__len = sum(len(hdict) for hdict in self.__table.values())

    def __contains__(self, x) -> bool:
        """
        Implements x in self. Returns True if x is itself in self.
        """
        if not isinstance(x, IsoSet.__Hashable):
            raise TypeError(f"unhashable type: '{type(x).__name__}'")
        h = hash(x)
        return h in self.__table and id(x) in self.__table[h]
    
    @property
    def iso_view(self) -> "IsoView[K]":
        """
        An IsoView of the set. It behaves like the IsoSet except set operations are based on equality.
        """
        return IsoView(self)
    
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
        
    def difference(self, *sets : Iterable[K]) -> "IsoSet[K]":
        """
        Return the difference of two or more sets as a new IsoSet.

        (i.e. all elements that are in this set but not the others.)
        """
        s = self.copy()
        for si in sets:
            if not isinstance(si, IsoSet.__Iterable):
                raise TypeError(f"Expected iterable, got '{type(si).__name__}'")
        for si in sets:
            for k in si:
                s.discard(k)
        return s
    
    def difference_update(self, *sets : Iterable[K]):
        """
        Remove all elements of another set from this IsoSet.
        """
        for si in sets:
            if not isinstance(si, IsoSet.__Iterable):
                raise TypeError(f"Expected iterable, got '{type(si).__name__}'")
        for si in sets:
            for k in si:
                self.discard(k)
    
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

    def intersection(self, *sets : Iterable[K]) -> "IsoSet[K]":
        """
        Return the difference of two or more sets as a new IsoSet.

        (i.e. all elements that are in this set but not the others.)
        """
        for si in sets:
            if not isinstance(si, IsoSet.__Iterable):
                raise TypeError(f"Expected iterable, got '{type(si).__name__}'")
        return self.difference(self.difference(*sets))
    
    def intersection_update(self, *sets : Iterable[K]):
        """
        Update an IsoSet with the intersection of itself and another.
        """
        for si in sets:
            if not isinstance(si, IsoSet.__Iterable):
                raise TypeError(f"Expected iterable, got '{type(si).__name__}'")
        self.difference_update(self.difference(*sets))
    
    def isdisjoint(self, s : Iterable[K]) -> bool:
        """
        Return True if two sets have a null intersection.
        """
        if not isinstance(s, IsoSet.__Iterable):
            raise TypeError(f"Expected iterable, got '{type(s).__name__}'")
        return all(k not in self for k in s)
    
    def issubset(self, s : Iterable[K]) -> bool:
        """
        Report whether another set contains this IsoSet.
        """
        if not isinstance(s, IsoSet.__Iterable):
            raise TypeError(f"Expected iterable, got '{type(s).__name__}'")
        s = IsoSet(s)
        return all(k in s for k in self)
    
    def issuperset(self, s : Iterable[K]) -> bool:
        """
        Report whether this IsoSet contains another set.
        """
        if not isinstance(s, IsoSet.__Iterable):
            raise TypeError(f"Expected iterable, got '{type(s).__name__}'")
        return all(k in self for k in s)
    
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
    
    def symmetric_difference(self, s : Iterable[K]) -> "IsoSet[K]":
        """
        Return the symmetric difference of two sets as a new set.

        (i.e. all elements that are in exactly one of the sets.)
        """
        if not isinstance(s, IsoSet.__Iterable):
            raise TypeError(f"Expected iterable, got '{type(s).__name__}'")
        res = self.copy()
        for k in s:
            if k in res:
                res.remove(k)
            else:
                res.add(k)
        return res
    
    def symmetric_difference_update(self, s : Iterable[K]):
        """
        Update an IsoSet with the symmetric difference of itself and another.
        """
        if not isinstance(s, IsoSet.__Iterable):
            raise TypeError(f"Expected iterable, got '{type(s).__name__}'")
        for k in s:
            if k in self:
                self.remove(k)
            else:
                self.add(k)

    def union(self, *sets : Iterable[K]) -> "IsoSet[K]":
        """
        Return the union of sets as a new set.

        (i.e. all elements that are in either set.)
        """
        s = self.copy()
        for si in sets:
            if not isinstance(si, IsoSet.__Iterable):
                raise TypeError(f"Expected iterable, got '{type(si).__name__}'")
        for si in sets:
            for k in si:
                s.add(k)
        return s
    
    def update(self, *sets : Iterable[K]):
        """
        Update an IsoSet with the union of itself and others.
        """
        for si in sets:
            if not isinstance(si, IsoSet.__Iterable):
                raise TypeError(f"Expected iterable, got '{type(si).__name__}'")
        for si in sets:
            for k in si:
                self.add(k)
    
    def __sizeof__(self) -> int:
        return super().__sizeof__() + IsoSet.__getsizeof(self.__table) + sum(IsoSet.__getsizeof(hdict) for hdict in self.__table.values())
        
    def __eq__(self, value: object) -> bool:
        if self is value:
            return True
        if not isinstance(value, IsoSet.__Set):
            return False
        return len(self) == len(value) and all(e in value for e in self)
    
    def __le__(self, other: Set[Any]) -> bool:
        if self is other:
            return True
        if not isinstance(other, IsoSet.__Set):
            raise TypeError(f"'<=' not supported between instances of '{type(self).__name__}' and '{type(other).__name__}'")
        if not isinstance(other, IsoSet):
            return len(self) <= len(other) and all(k in other for k in self)
        return (self.__table.keys() <= other.__table.keys()) and all(self.__table[h].keys() <= other.__table[h].keys() for h in self.__table.keys())
    
    def __lt__(self, other: Set[Any]) -> bool:
        if self is other:
            return False
        if not isinstance(other, IsoSet.__Set):
            raise TypeError(f"'<' not supported between instances of '{type(self).__name__}' and '{type(other).__name__}'")
        if not isinstance(other, IsoSet):
            return len(self) < len(other) and all(k in other for k in self)
        return self <= other and len(self) != len(other)
    
    def __ge__(self, other: Set[Any]) -> bool:
        if self is other:
            return True
        if not isinstance(other, IsoSet.__Set):
            raise TypeError(f"'>=' not supported between instances of '{type(self).__name__}' and '{type(other).__name__}'")
        if not isinstance(other, IsoSet):
            return len(self) >= len(other) and all(k in self for k in other)
        return (self.__table.keys() >= other.__table.keys()) and all(self.__table[h].keys() >= other.__table[h].keys() for h in other.__table.keys())
    
    def __gt__(self, other: Set[Any]) -> bool:
        if self is other:
            return False
        if not isinstance(other, IsoSet.__Set):
            raise TypeError(f"'>' not supported between instances of '{type(self).__name__}' and '{type(other).__name__}'")
        if not isinstance(other, IsoSet):
            return len(self) >= len(other) and all(k in self for k in other)
        return self >= other and len(self) != len(other)
    
    def __and__(self, other : Set[K]) -> "IsoSet[K]":
        if not isinstance(other, IsoSet.__Set):
            return NotImplemented
        if len(self) > len(other):
            return IsoSet(k for k in other if k in self)
        else:
            return IsoSet(k for k in self if k in other)
    
    def __rand__(self, other : Set[K]) -> "IsoSet[K]":
        if not isinstance(other, IsoSet.__Set):
            return NotImplemented
        if len(self) > len(other):
            return IsoSet(k for k in other if k in self)
        else:
            return IsoSet(k for k in self if k in other)
        
    def __iand__(self, other : Set[K]) -> "IsoSet[K]":
        if not isinstance(other, IsoSet.__Set):
            return NotImplemented
        for k in self.copy():
            if k not in other:
                self.remove(k)
        return self
    
    def __or__(self, other : Set[K]) -> "IsoSet[K]":
        if not isinstance(other, IsoSet.__Set):
            return NotImplemented
        s = IsoSet(self)
        for k in other:
            s.add(k)
        return s
    
    def __ror__(self, other : Set[K]) -> "IsoSet[K]":
        if not isinstance(other, IsoSet.__Set):
            return NotImplemented
        s = IsoSet(self)
        for k in other:
            s.add(k)
        return s
    
    def __ior__(self, other : Set[K]) -> "IsoSet[K]":
        if not isinstance(other, IsoSet.__Set):
            return NotImplemented
        for k in other:
            self.add(k)
        return self
    
    def __sub__(self, other : Set[K]) -> "IsoSet[K]":
        if not isinstance(other, IsoSet.__Set):
            return NotImplemented
        return IsoSet(k for k in self if k not in other)
    
    def __rsub__(self, other : Set[K]) -> "IsoSet[K]":
        if not isinstance(other, IsoSet.__Set):
            return NotImplemented
        return IsoSet(k for k in other if k not in self)
    
    def __isub__(self, other : Set[K]) -> "IsoSet[K]":
        if not isinstance(other, IsoSet.__Set):
            return NotImplemented
        for k in other:
            self.discard(k)
        return self
    
    def __xor__(self, other : Set[K]) -> "IsoSet[K]":
        if not isinstance(other, IsoSet.__Set):
            return NotImplemented
        s = IsoSet()
        for k in self:
            if k not in other:
                s.add(k)
        for k in other:
            if k not in self:
                s.add(k)
        return s
    
    def __rxor__(self, other : Set[K]) -> "IsoSet[K]":
        if not isinstance(other, IsoSet.__Set):
            return NotImplemented
        s = IsoSet()
        for k in self:
            if k not in other:
                s.add(k)
        for k in other:
            if k not in self:
                s.add(k)
        return s
    
    def __ixor__(self, other : Set[K]) -> "IsoSet[K]":
        if not isinstance(other, IsoSet.__Set):
            return NotImplemented
        for k in other:
            if k in self:
                self.remove(k)
            else:
                self.add(k)
        return self
    




class FrozenIsoSet(Set[K]):

    """
    Frozen (immutable) version of IsoSets.
    """

    from collections.abc import Set as __Set, Iterable as __Iterable, Hashable as __Hashable
    from sys import getsizeof
    __getsizeof = staticmethod(getsizeof)
    del getsizeof

    __slots__ = {
        "__table" : "The association table used to store all the elements of the FrozenIsoSet.",
        "__len" : "The size of the FrozenIsoSet.",
        "__hash" : "A cache for the computed hash."
    }

    def __init__(self, iterable : Iterable[K] = ()) -> None:
        if not isinstance(iterable, FrozenIsoSet.__Iterable):
            raise TypeError(f"Expected iterable, got '{type(iterable).__name__}'")
        
        self.__table : "dict[int, dict[int, K]]" = {}
        for t in iterable:
            if not isinstance(t, FrozenIsoSet.__Hashable):
                raise TypeError(f"unhashable type: '{type(t).__name__}'")
            self.__table.setdefault(hash(t), {})[id(t)] = t
        self.__len = sum(len(hdict) for hdict in self.__table.values())
        self.__hash : int | None = None

    def __getstate__(self):
        return {"data" : list(self)}

    def __setstate__(self, state):
        self.__table : "dict[int, dict[int, K]]" = {}
        for t in state["data"]:
            self.__table.setdefault(hash(t), {})[id(t)] = t # type: ignore
        self.__len = sum(len(hdict) for hdict in self.__table.values())
        self.__hash = None
                
    def __repr__(self) -> str:
        return f"{type(self).__name__}([{', '.join(repr(e) for e in self)}])"
    
    def __str__(self) -> str:
        return f"{type(self).__name__}([{', '.join(repr(e) for e in self)}])"

    def __contains__(self, x) -> bool:
        """
        Implements x in self. Returns True if x is itself in self.
        """
        if not isinstance(x, FrozenIsoSet.__Hashable):
            raise TypeError(f"unhashable type: '{type(x).__name__}'")
        h = hash(x)
        return h in self.__table and id(x) in self.__table[h]
    
    @property
    def iso_view(self) -> "FrozenIsoView[K]":
        """
        An IsoView of the set. It behaves like the FrozenIsoSet except set operations are based on equality.
        """
        return FrozenIsoView(self)
    
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
    
    def copy(self) -> "FrozenIsoSet[K]":
        """
        Return a shallow copy of an FrozenIsoSet.
        """
        cp = FrozenIsoSet()
        cp.__table = {h : hdict.copy() for h, hdict in self.__table.items()}
        cp.__len = self.__len
        return cp
        
    def difference(self, *sets : Iterable[K]) -> "FrozenIsoSet[K]":
        """
        Return the difference of two or more sets as a new FrozenIsoSet.

        (i.e. all elements that are in this set but not the others.)
        """
        s = self.copy()
        for si in sets:
            if not isinstance(si, FrozenIsoSet.__Iterable):
                raise TypeError(f"Expected iterable, got '{type(si).__name__}'")
        for si in sets:
            for k in si:
                if k not in s:
                    continue
                h = hash(k)
                hdict = s.__table[h]
                hdict.pop(id(k))
                s.__len -= 1
                if not hdict:
                    s.__table.pop(h)
        return s
    
    def intersection(self, *sets : Iterable[K]) -> "FrozenIsoSet[K]":
        """
        Return the difference of two or more sets as a new FrozenIsoSet.

        (i.e. all elements that are in this set but not the others.)
        """
        for si in sets:
            if not isinstance(si, FrozenIsoSet.__Iterable):
                raise TypeError(f"Expected iterable, got '{type(si).__name__}'")
        return self.difference(self.difference(*sets))
    
    def isdisjoint(self, s : Iterable[K]) -> bool:
        """
        Return True if two sets have a null intersection.
        """
        if not isinstance(s, FrozenIsoSet.__Iterable):
            raise TypeError(f"Expected iterable, got '{type(s).__name__}'")
        return all(k not in self for k in s)
    
    def issubset(self, s : Iterable[K]) -> bool:
        """
        Report whether another set contains this FrozenIsoSet.
        """
        if not isinstance(s, FrozenIsoSet.__Iterable):
            raise TypeError(f"Expected iterable, got '{type(s).__name__}'")
        s = FrozenIsoSet(s)
        return all(k in s for k in self)
    
    def issuperset(self, s : Iterable[K]) -> bool:
        """
        Report whether this FrozenIsoSet contains another set.
        """
        if not isinstance(s, FrozenIsoSet.__Iterable):
            raise TypeError(f"Expected iterable, got '{type(s).__name__}'")
        return all(k in self for k in s)
    
    def symmetric_difference(self, s : Iterable[K]) -> "FrozenIsoSet[K]":
        """
        Return the symmetric difference of two sets as a new set.

        (i.e. all elements that are in exactly one of the sets.)
        """
        if not isinstance(s, FrozenIsoSet.__Iterable):
            raise TypeError(f"Expected iterable, got '{type(s).__name__}'")
        res = self.copy()
        for k in s:
            if k in res:
                h = hash(k)
                hdict = res.__table[h]
                hdict.pop(id(k))
                res.__len -= 1
                if not hdict:
                    res.__table.pop(h)
            else:
                res.__table.setdefault(hash(k), {})[id(k)] = k
        return res

    def union(self, *sets : Iterable[K]) -> "FrozenIsoSet[K]":
        """
        Return the union of sets as a new set.

        (i.e. all elements that are in either set.)
        """
        s = self.copy()
        for si in sets:
            if not isinstance(si, FrozenIsoSet.__Iterable):
                raise TypeError(f"Expected iterable, got '{type(si).__name__}'")
        for si in sets:
            for k in si:
                s.__table.setdefault(hash(k), {})[id(k)] = k
        return s
    
    def __sizeof__(self) -> int:
        return super().__sizeof__() + FrozenIsoSet.__getsizeof(self.__table) + sum(FrozenIsoSet.__getsizeof(hdict) for hdict in self.__table.values())
    
    def __hash__(self) -> int:
        """
        Implements hash(self).
        """
        if self.__hash is None:
            self.__hash = hash(-len(self) + sum(hash(k) for k in self))
        return self.__hash
    
    def __eq__(self, value: object) -> bool:
        if self is value:
            return True
        if not isinstance(value, FrozenIsoSet.__Set):
            return False
        return len(self) == len(value) and all(e in value for e in self)
    
    def __le__(self, other: Set[Any]) -> bool:
        if self is other:
            return True
        if not isinstance(other, FrozenIsoSet.__Set):
            raise TypeError(f"'<=' not supported between instances of '{type(self).__name__}' and '{type(other).__name__}'")
        if not isinstance(other, FrozenIsoSet):
            return len(self) <= len(other) and all(k in other for k in self)
        return (self.__table.keys() <= other.__table.keys()) and all(self.__table[h].keys() <= other.__table[h].keys() for h in self.__table.keys())
    
    def __lt__(self, other: Set[Any]) -> bool:
        if self is other:
            return False
        if not isinstance(other, FrozenIsoSet.__Set):
            raise TypeError(f"'<' not supported between instances of '{type(self).__name__}' and '{type(other).__name__}'")
        if not isinstance(other, FrozenIsoSet):
            return len(self) < len(other) and all(k in other for k in self)
        return self <= other and len(self) != len(other)
    
    def __ge__(self, other: Set[Any]) -> bool:
        if self is other:
            return True
        if not isinstance(other, FrozenIsoSet.__Set):
            raise TypeError(f"'>=' not supported between instances of '{type(self).__name__}' and '{type(other).__name__}'")
        if not isinstance(other, FrozenIsoSet):
            return len(self) >= len(other) and all(k in self for k in other)
        return (self.__table.keys() >= other.__table.keys()) and all(self.__table[h].keys() >= other.__table[h].keys() for h in other.__table.keys())
    
    def __gt__(self, other: Set[Any]) -> bool:
        if self is other:
            return False
        if not isinstance(other, FrozenIsoSet.__Set):
            raise TypeError(f"'>' not supported between instances of '{type(self).__name__}' and '{type(other).__name__}'")
        if not isinstance(other, FrozenIsoSet):
            return len(self) >= len(other) and all(k in self for k in other)
        return self >= other and len(self) != len(other)
    
    def __and__(self, other : Set[K]) -> "FrozenIsoSet[K]":
        if not isinstance(other, FrozenIsoSet.__Set):
            return NotImplemented
        if len(self) > len(other):
            return FrozenIsoSet(k for k in other if k in self)
        else:
            return FrozenIsoSet(k for k in self if k in other)
    
    def __rand__(self, other : Set[K]) -> "FrozenIsoSet[K]":
        if not isinstance(other, FrozenIsoSet.__Set):
            return NotImplemented
        if len(self) > len(other):
            return FrozenIsoSet(k for k in other if k in self)
        else:
            return FrozenIsoSet(k for k in self if k in other)
            
    def __or__(self, other : Set[K]) -> "FrozenIsoSet[K]":
        if not isinstance(other, FrozenIsoSet.__Set):
            return NotImplemented
        s = FrozenIsoSet(self)
        for k in other:
            s.__table.setdefault(hash(k), {})[id(k)] = k
        return s
    
    def __ror__(self, other : Set[K]) -> "FrozenIsoSet[K]":
        if not isinstance(other, FrozenIsoSet.__Set):
            return NotImplemented
        s = FrozenIsoSet(self)
        for k in other:
            s.__table.setdefault(hash(k), {})[id(k)] = k
        return s
        
    def __sub__(self, other : Set[K]) -> "FrozenIsoSet[K]":
        if not isinstance(other, FrozenIsoSet.__Set):
            return NotImplemented
        return FrozenIsoSet(k for k in self if k not in other)
    
    def __rsub__(self, other : Set[K]) -> "FrozenIsoSet[K]":
        if not isinstance(other, FrozenIsoSet.__Set):
            return NotImplemented
        return FrozenIsoSet(k for k in other if k not in self)
    
    def __xor__(self, other : Set[K]) -> "FrozenIsoSet[K]":
        if not isinstance(other, FrozenIsoSet.__Set):
            return NotImplemented
        s = FrozenIsoSet()
        for k in self:
            if k not in other:
                s.__table.setdefault(hash(k), {})[id(k)] = k
        for k in other:
            if k not in self:
                s.__table.setdefault(hash(k), {})[id(k)] = k
        return s
    
    def __rxor__(self, other : Set[K]) -> "FrozenIsoSet[K]":
        if not isinstance(other, FrozenIsoSet.__Set):
            return NotImplemented
        s = FrozenIsoSet()
        for k in self:
            if k not in other:
                s.__table.setdefault(hash(k), {})[id(k)] = k
        for k in other:
            if k not in self:
                s.__table.setdefault(hash(k), {})[id(k)] = k
        return s
    




class IsoView(MutableSet[K]):

    """
    A view of an IsoSet that compare equal elements in set operations (using elements' '__eq__' methods, for operators 'in', ==, !=, <, <=, >, >=). Behaves like an IsoSet otherwise.
    To switch between set comparison rules, use IsoSet.iso_view and IsoView.iso_set.
    These special operations only work between IsoViews, falling back to IsoSet operations if one operand is not an IsoView.
    """

    from collections.abc import Set as __Set, Iterable as __Iterable, Hashable as __Hashable

    __slots__ = {
        "__table" : "The association table used to store all the elements of the IsoSet.",
        "__set" : "The original IsoSet."
    }

    def __init__(self, isoset : IsoSet[K]) -> None:
        self.__set = isoset
        self.__table : "dict[int, dict[int, K]]" = isoset._IsoSet__table # type: ignore

    @property
    def set(self) -> IsoSet[K]:
        """
        The original IsoSet referred to by this view.
        """
        return self.__set

    def __repr__(self) -> str:
        return f"{type(self).__name__}([{', '.join(repr(e) for e in self)}])"
    
    def __str__(self) -> str:
        return f"{type(self).__name__}([{', '.join(repr(e) for e in self)}])"

    def __contains__(self, x) -> bool:
        """
        Implements x in self. Returns True if x is itself in self or if an element of self equals x.
        """
        if not isinstance(x, IsoView.__Hashable):
            raise TypeError(f"unhashable type: '{type(x).__name__}'")
        h = hash(x)
        return h in self.__table and (id(x) in self.__table[h] or any(x == v for v in self.__table[h].values()))
    
    def __iter__(self) -> Iterator[K]:
        """
        Implements iter(self).
        """
        return iter(self.__set)

    def __len__(self) -> int:
        """
        Implements len(self).
        """
        return len(self.__set)
    
    def __bool__(self) -> bool:
        """
        Implements bool(self).
        """
        return bool(self.__set)
    
    def add(self, value: K) -> None:
        if not isinstance(value, IsoView.__Hashable):
            raise TypeError(f"unhashable type: '{type(value).__name__}'")
        self.__set.add(value)

    def clear(self) -> None:
        self.__set.clear()

    def copy(self) -> "IsoView[K]":
        """
        Return a shallow copy of an IsoView.
        """
        return IsoView(self.__set.copy())
        
    def difference(self, *sets : Iterable[K]) -> "IsoView[K]":
        """
        Return the difference of two or more sets as a new IsoView.

        (i.e. all elements that are in this set but not the others.)
        """
        for si in sets:
            if not isinstance(si, IsoView.__Iterable):
                raise TypeError(f"Expected iterable, got '{type(si).__name__}'")
        return IsoView(self.__set.difference(*sets))
    
    def difference_update(self, *sets : Iterable[K]):
        """
        Remove all elements of another set from this IsoView.
        """
        for si in sets:
            if not isinstance(si, IsoView.__Iterable):
                raise TypeError(f"Expected iterable, got '{type(si).__name__}'")
        self.__set.difference_update(*sets)
    
    def discard(self, value: K) -> None:
        if not isinstance(value, IsoView.__Hashable):
            raise TypeError(f"unhashable type: '{type(value).__name__}'")
        self.__set.discard(value)

    def intersection(self, *sets : Iterable[K]) -> "IsoView[K]":
        """
        Return the difference of two or more sets as a new IsoView.

        (i.e. all elements that are in this set but not the others.)
        """
        for si in sets:
            if not isinstance(si, IsoView.__Iterable):
                raise TypeError(f"Expected iterable, got '{type(si).__name__}'")
        return IsoView(self.__set.intersection(*sets))
    
    def intersection_update(self, *sets : Iterable[K]):
        """
        Update an IsoView with the intersection of itself and another.
        """
        for si in sets:
            if not isinstance(si, IsoView.__Iterable):
                raise TypeError(f"Expected iterable, got '{type(si).__name__}'")
        self.__set.intersection_update(*sets)
    
    def isdisjoint(self, s : Iterable[K]) -> bool:
        """
        Return True if two sets have a null intersection.
        """
        if not isinstance(s, IsoView.__Iterable):
            raise TypeError(f"Expected iterable, got '{type(s).__name__}'")
        return bool(self.__set.isdisjoint(s))
    
    def issubset(self, s : Iterable[K]) -> bool:
        """
        Report whether another set contains this IsoView.
        """
        if not isinstance(s, IsoView.__Iterable):
            raise TypeError(f"Expected iterable, got '{type(s).__name__}'")
        return self.__set.issubset(s)
    
    def issuperset(self, s : Iterable[K]) -> bool:
        """
        Report whether this IsoView contains another set.
        """
        if not isinstance(s, IsoView.__Iterable):
            raise TypeError(f"Expected iterable, got '{type(s).__name__}'")
        return self.__set.issuperset(s)
    
    def pop(self) -> K:
        """
        Remove and return an arbitrary IsoView element.
        Raises KeyError if the IsoView is empty.
        """
        if not self:
            raise KeyError("'pop from empty IsoView'")
        return self.__set.pop()
        
    def remove(self, e : K):
        """
        Remove an element from an IsoView; it must be a member.

        If the element is not a member, raise a KeyError.
        """
        if e in self.__set:
            self.__set.discard(e)
        else:
            raise KeyError(repr(e))
    
    def symmetric_difference(self, s : Iterable[K]) -> "IsoView[K]":
        """
        Return the symmetric difference of two sets as a new IsoView.

        (i.e. all elements that are in exactly one of the sets.)
        """
        if not isinstance(s, IsoView.__Iterable):
            raise TypeError(f"Expected iterable, got '{type(s).__name__}'")
        return IsoView(self.__set.symmetric_difference(s))
    
    def symmetric_difference_update(self, s : Iterable[K]):
        """
        Update an IsoView with the symmetric difference of itself and another.
        """
        if not isinstance(s, IsoView.__Iterable):
            raise TypeError(f"Expected iterable, got '{type(s).__name__}'")
        self.__set.symmetric_difference_update(s)

    def union(self, *sets : Iterable[K]) -> "IsoView[K]":
        """
        Return the union of sets as a new IsoView.

        (i.e. all elements that are in either set.)
        """
        for si in sets:
            if not isinstance(si, IsoView.__Iterable):
                raise TypeError(f"Expected iterable, got '{type(si).__name__}'")
        return IsoView(self.__set.union(*sets))
    
    def update(self, *sets : Iterable[K]):
        """
        Update an IsoView with the union of itself and others.
        """
        for si in sets:
            if not isinstance(si, IsoView.__Iterable):
                raise TypeError(f"Expected iterable, got '{type(si).__name__}'")
        self.__set.update(*sets)
    
    def __sizeof__(self) -> int:
        return object.__sizeof__(self)
    
    def __getstate__(self) -> object:
        return {
            "__table" : self.__table,
            "__set" : self.__set,
            }
    
    def __eq__(self, value: object) -> bool:
        if self is value:
            return True
        if not isinstance(value, IsoView.__Set):
            return False
        if not isinstance(value, IsoView):
            return self.__set == value
        if len(self.__set) != len(value.__set):
            return False
        for h, self_hdict in self.__table.items():
            value_hdict : "dict[int, K]" = value.__table.get(h, {})
            value_hdict, self_hdict = {i : k for i, k in value_hdict.items() if i not in self_hdict}, {i : k for i, k in self_hdict.items() if i not in value_hdict}    # Skipping identical elements
            if len(self_hdict) != len(value_hdict):
                return False
            while self_hdict:
                ia, a = self_hdict.popitem()
                for ib, b in value_hdict.items():
                    if a == b:
                        value_hdict.pop(ib)
                        break
                else:
                    return False
        return True
    
    def __le__(self, other: Set[Any]) -> bool:
        if self is other:
            return True
        if not isinstance(other, IsoView.__Set):
            raise TypeError(f"'<=' not supported between instances of '{type(self).__name__}' and '{type(other).__name__}'")
        if not isinstance(other, IsoView):
            return self.__set <= other
        if len(self.__set) > len(other.__set):
            return False
        for h, self_hdict in self.__table.items():
            other_hdict : "dict[int, K]" = other.__table.get(h, {})
            other_hdict, self_hdict = {i : k for i, k in other_hdict.items() if i not in self_hdict}, {i : k for i, k in self_hdict.items() if i not in other_hdict}    # Skipping identical elements
            if len(self_hdict) > len(other_hdict):
                return False
            while self_hdict:
                ia, a = self_hdict.popitem()
                for ib, b in other_hdict.items():
                    if a == b:
                        other_hdict.pop(ib)
                        break
                else:
                    return False
        return True
    
    def __lt__(self, other: Set[Any]) -> bool:
        if self is other:
            return False
        if not isinstance(other, IsoView.__Set):
            raise TypeError(f"'<' not supported between instances of '{type(self).__name__}' and '{type(other).__name__}'")
        if not isinstance(other, IsoView):
            return self.__set < other
        if len(self.__set) >= len(other.__set):
            return False
        for h, self_hdict in self.__table.items():
            other_hdict : "dict[int, K]" = other.__table.get(h, {})
            other_hdict, self_hdict = {i : k for i, k in other_hdict.items() if i not in self_hdict}, {i : k for i, k in self_hdict.items() if i not in other_hdict}    # Skipping identical elements
            if len(self_hdict) > len(other_hdict):
                return False
            while self_hdict:
                ia, a = self_hdict.popitem()
                for ib, b in other_hdict.items():
                    if a == b:
                        other_hdict.pop(ib)
                        break
                else:
                    return False
        return True
    
    def __ge__(self, other: Set[Any]) -> bool:
        if self is other:
            return True
        if not isinstance(other, IsoView.__Set):
            raise TypeError(f"'>=' not supported between instances of '{type(self).__name__}' and '{type(other).__name__}'")
        if not isinstance(other, IsoView):
            return self.__set >= other
        if len(self.__set) < len(other.__set):
            return False
        return other <= self
    
    def __gt__(self, other: Set[Any]) -> bool:
        if self is other:
            return False
        if not isinstance(other, IsoView.__Set):
            raise TypeError(f"'>' not supported between instances of '{type(self).__name__}' and '{type(other).__name__}'")
        if not isinstance(other, IsoView):
            return self.__set > other
        if len(self.__set) <= len(other.__set):
            return False
        return other < self
    
    def __and__(self, other : Set[K]) -> "IsoView[K]":
        if not isinstance(other, IsoView.__Set):
            return NotImplemented
        return IsoView(self.__set & other)
    
    def __rand__(self, other : Set[K]) -> "IsoView[K]":
        if not isinstance(other, IsoView.__Set):
            return NotImplemented
        r = other & self.__set
        if not isinstance(r, IsoSet):
            r = IsoSet(r)
        return IsoView(r)
        
    def __iand__(self, other : Set[K]) -> "IsoView[K]":
        if not isinstance(other, IsoView.__Set):
            return NotImplemented
        self.__set &= other
        return self
    
    def __or__(self, other : Set[K]) -> "IsoView[K]":
        if not isinstance(other, IsoView.__Set):
            return NotImplemented
        return IsoView(self.__set | other)
    
    def __ror__(self, other : Set[K]) -> "IsoView[K]":
        if not isinstance(other, IsoView.__Set):
            return NotImplemented
        r = other | self.__set
        if not isinstance(r, IsoSet):
            r = IsoSet(r)
        return IsoView(r)
    
    def __ior__(self, other : Set[K]) -> "IsoView[K]":
        if not isinstance(other, IsoView.__Set):
            return NotImplemented
        self.__set |= other
        return self
    
    def __sub__(self, other : Set[K]) -> "IsoView[K]":
        if not isinstance(other, IsoView.__Set):
            return NotImplemented
        return IsoView(self.__set - other)
    
    def __rsub__(self, other : Set[K]) -> "IsoView[K]":
        if not isinstance(other, IsoView.__Set):
            return NotImplemented
        r = other - self.__set
        if not isinstance(r, IsoSet):
            r = IsoSet(r)
        return IsoView(r)
    
    def __isub__(self, other : Set[K]) -> "IsoView[K]":
        if not isinstance(other, IsoView.__Set):
            return NotImplemented
        self.__set -= other
        return self
    
    def __xor__(self, other : Set[K]) -> "IsoView[K]":
        if not isinstance(other, IsoView.__Set):
            return NotImplemented
        return IsoView(self.__set ^ other)
    
    def __rxor__(self, other : Set[K]) -> "IsoView[K]":
        if not isinstance(other, IsoView.__Set):
            return NotImplemented
        r = other ^ self.__set
        if not isinstance(r, IsoSet):
            r = IsoSet(r)
        return IsoView(r)
    
    def __ixor__(self, other : Set[K]) -> "IsoView[K]":
        if not isinstance(other, IsoView.__Set):
            return NotImplemented
        self.__set ^= other
        return self
    




class FrozenIsoView(Set[K]):

    """
    A view of a FrozenIsoSet that compare equal elements in set operations (using elements' '__eq__' methods, for operators 'in', ==, !=, <, <=, >, >=). Behaves like a FrozenIsoSet otherwise.
    To switch between set comparison rules, use FrozenIsoSet.iso_view and FrozenIsoView.iso_set.
    These special operations only work between IsoViews, falling back to IsoSet operations if one operand is not an IsoView.
    """

    from collections.abc import Set as __Set, Iterable as __Iterable, Hashable as __Hashable

    __slots__ = {
        "__table" : "The association table used to store all the elements of the FrozenIsoSet.",
        "__set" : "The original FrozenIsoSet."
    }

    def __init__(self, isoset : FrozenIsoSet[K]) -> None:
        self.__set = isoset
        self.__table : "dict[int, dict[int, K]]" = isoset._IsoSet__table # type: ignore

    @property
    def set(self) -> FrozenIsoSet[K]:
        """
        The original FrozenIsoSet referred to by this view.
        """
        return self.__set

    def __repr__(self) -> str:
        return f"{type(self).__name__}([{', '.join(repr(e) for e in self)}])"
    
    def __str__(self) -> str:
        return f"{type(self).__name__}([{', '.join(repr(e) for e in self)}])"

    def __contains__(self, x) -> bool:
        """
        Implements x in self. Returns True if x is itself in self or if an element of self equals x.
        """
        if not isinstance(x, FrozenIsoView.__Hashable):
            raise TypeError(f"unhashable type: '{type(x).__name__}'")
        h = hash(x)
        return h in self.__table and (id(x) in self.__table[h] or any(x == v for v in self.__table[h].values()))
    
    def __iter__(self) -> Iterator[K]:
        """
        Implements iter(self).
        """
        return iter(self.__set)

    def __len__(self) -> int:
        """
        Implements len(self).
        """
        return len(self.__set)
    
    def __bool__(self) -> bool:
        """
        Implements bool(self).
        """
        return bool(self.__set)
    
    def copy(self) -> "FrozenIsoView[K]":
        """
        Return a shallow copy of a FrozenIsoView.
        """
        return FrozenIsoView(self.__set.copy())
        
    def difference(self, *sets : Iterable[K]) -> "FrozenIsoView[K]":
        """
        Return the difference of two or more sets as a new FrozenIsoView.

        (i.e. all elements that are in this set but not the others.)
        """
        for si in sets:
            if not isinstance(si, FrozenIsoView.__Iterable):
                raise TypeError(f"Expected iterable, got '{type(si).__name__}'")
        return FrozenIsoView(self.__set.difference(*sets))
    
    def intersection(self, *sets : Iterable[K]) -> "FrozenIsoView[K]":
        """
        Return the difference of two or more sets as a new FrozenIsoView.

        (i.e. all elements that are in this set but not the others.)
        """
        for si in sets:
            if not isinstance(si, FrozenIsoView.__Iterable):
                raise TypeError(f"Expected iterable, got '{type(si).__name__}'")
        return FrozenIsoView(self.__set.intersection(*sets))
    
    def isdisjoint(self, s : Iterable[K]) -> bool:
        """
        Return True if two sets have a null intersection.
        """
        if not isinstance(s, FrozenIsoView.__Iterable):
            raise TypeError(f"Expected iterable, got '{type(s).__name__}'")
        return bool(self.__set.isdisjoint(s))
    
    def issubset(self, s : Iterable[K]) -> bool:
        """
        Report whether another set contains this FrozenIsoView.
        """
        if not isinstance(s, FrozenIsoView.__Iterable):
            raise TypeError(f"Expected iterable, got '{type(s).__name__}'")
        return self.__set.issubset(s)
    
    def issuperset(self, s : Iterable[K]) -> bool:
        """
        Report whether this FrozenIsoView contains another set.
        """
        if not isinstance(s, FrozenIsoView.__Iterable):
            raise TypeError(f"Expected iterable, got '{type(s).__name__}'")
        return self.__set.issuperset(s)
    
    def symmetric_difference(self, s : Iterable[K]) -> "FrozenIsoView[K]":
        """
        Return the symmetric difference of two sets as a new FrozenIsoView.

        (i.e. all elements that are in exactly one of the sets.)
        """
        if not isinstance(s, FrozenIsoView.__Iterable):
            raise TypeError(f"Expected iterable, got '{type(s).__name__}'")
        return FrozenIsoView(self.__set.symmetric_difference(s))

    def union(self, *sets : Iterable[K]) -> "FrozenIsoView[K]":
        """
        Return the union of sets as a new FrozenIsoView.

        (i.e. all elements that are in either set.)
        """
        for si in sets:
            if not isinstance(si, FrozenIsoView.__Iterable):
                raise TypeError(f"Expected iterable, got '{type(si).__name__}'")
        return FrozenIsoView(self.__set.union(*sets))
    
    def __sizeof__(self) -> int:
        return object.__sizeof__(self)
    
    def __getstate__(self) -> object:
        return {
            "__table" : self.__table,
            "__set" : self.__set,
            }

    @staticmethod
    def __from_view(v : IsoView[K]) -> "FrozenIsoView[K]":
        """
        Internal method used to avoid copying IsoView into FrozenIsoViews when comparaing.
        """
        f = FrozenIsoView(FrozenIsoSet())
        f.__set = v.set
        f.__table = v._IsoView__table # type: ignore
        return f
    
    def __hash__(self) -> int:
        """
        Implements hash(self):
        """
        return hash(-hash(self.__set))
    
    def __eq__(self, value: object) -> bool:
        if self is value:
            return True
        if not isinstance(value, FrozenIsoView.__Set):
            return False
        if isinstance(value, IsoView):
            value = self.__from_view(value)
        if not isinstance(value, FrozenIsoView):
            return self.__set == value
        if len(self.__set) != len(value.__set):
            return False
        for h, self_hdict in self.__table.items():
            value_hdict : "dict[int, K]" = value.__table.get(h, {})
            value_hdict, self_hdict = {i : k for i, k in value_hdict.items() if i not in self_hdict}, {i : k for i, k in self_hdict.items() if i not in value_hdict}    # Skipping identical elements
            if len(self_hdict) != len(value_hdict):
                return False
            while self_hdict:
                ia, a = self_hdict.popitem()
                for ib, b in value_hdict.items():
                    if a == b:
                        value_hdict.pop(ib)
                        break
                else:
                    return False
        return True
    
    def __le__(self, other: Set[Any]) -> bool:
        if self is other:
            return True
        if not isinstance(other, FrozenIsoView.__Set):
            raise TypeError(f"'<=' not supported between instances of '{type(self).__name__}' and '{type(other).__name__}'")
        if isinstance(other, IsoView):
            other = self.__from_view(other)
        if not isinstance(other, FrozenIsoView):
            return self.__set <= other
        if len(self.__set) > len(other.__set):
            return False
        for h, self_hdict in self.__table.items():
            other_hdict : "dict[int, K]" = other.__table.get(h, {})
            other_hdict, self_hdict = {i : k for i, k in other_hdict.items() if i not in self_hdict}, {i : k for i, k in self_hdict.items() if i not in other_hdict}    # Skipping identical elements
            if len(self_hdict) > len(other_hdict):
                return False
            while self_hdict:
                ia, a = self_hdict.popitem()
                for ib, b in other_hdict.items():
                    if a == b:
                        other_hdict.pop(ib)
                        break
                else:
                    return False
        return True
    
    def __lt__(self, other: Set[Any]) -> bool:
        if self is other:
            return False
        if not isinstance(other, FrozenIsoView.__Set):
            raise TypeError(f"'<' not supported between instances of '{type(self).__name__}' and '{type(other).__name__}'")
        if isinstance(other, IsoView):
            other = self.__from_view(other)
        if not isinstance(other, FrozenIsoView):
            return self.__set < other
        if len(self.__set) >= len(other.__set):
            return False
        for h, self_hdict in self.__table.items():
            other_hdict : "dict[int, K]" = other.__table.get(h, {})
            other_hdict, self_hdict = {i : k for i, k in other_hdict.items() if i not in self_hdict}, {i : k for i, k in self_hdict.items() if i not in other_hdict}    # Skipping identical elements
            if len(self_hdict) > len(other_hdict):
                return False
            while self_hdict:
                ia, a = self_hdict.popitem()
                for ib, b in other_hdict.items():
                    if a == b:
                        other_hdict.pop(ib)
                        break
                else:
                    return False
        return True
    
    def __ge__(self, other: Set[Any]) -> bool:
        if self is other:
            return True
        if not isinstance(other, FrozenIsoView.__Set):
            raise TypeError(f"'>=' not supported between instances of '{type(self).__name__}' and '{type(other).__name__}'")
        if isinstance(other, IsoView):
            other = self.__from_view(other)
        if not isinstance(other, FrozenIsoView):
            return self.__set >= other
        if len(self.__set) < len(other.__set):
            return False
        return other <= self
    
    def __gt__(self, other: Set[Any]) -> bool:
        if self is other:
            return False
        if not isinstance(other, FrozenIsoView.__Set):
            raise TypeError(f"'>' not supported between instances of '{type(self).__name__}' and '{type(other).__name__}'")
        if isinstance(other, IsoView):
            other = self.__from_view(other)
        if not isinstance(other, FrozenIsoView):
            return self.__set > other
        if len(self.__set) <= len(other.__set):
            return False
        return other < self
    
    def __and__(self, other : Set[K]) -> "FrozenIsoView[K]":
        if not isinstance(other, FrozenIsoView.__Set):
            return NotImplemented
        return FrozenIsoView(self.__set & other)
    
    def __rand__(self, other : Set[K]) -> "FrozenIsoView[K]":
        if not isinstance(other, FrozenIsoView.__Set):
            return NotImplemented
        r = other & self.__set
        if not isinstance(r, FrozenIsoSet):
            r = FrozenIsoSet(r)
        return FrozenIsoView(r)
            
    def __or__(self, other : Set[K]) -> "FrozenIsoView[K]":
        if not isinstance(other, FrozenIsoView.__Set):
            return NotImplemented
        return FrozenIsoView(self.__set | other)
    
    def __ror__(self, other : Set[K]) -> "FrozenIsoView[K]":
        if not isinstance(other, FrozenIsoView.__Set):
            return NotImplemented
        r = other | self.__set
        if not isinstance(r, FrozenIsoSet):
            r = FrozenIsoSet(r)
        return FrozenIsoView(r)
    
    def __sub__(self, other : Set[K]) -> "FrozenIsoView[K]":
        if not isinstance(other, FrozenIsoView.__Set):
            return NotImplemented
        return FrozenIsoView(self.__set - other)
    
    def __rsub__(self, other : Set[K]) -> "FrozenIsoView[K]":
        if not isinstance(other, FrozenIsoView.__Set):
            return NotImplemented
        r = other - self.__set
        if not isinstance(r, FrozenIsoSet):
            r = FrozenIsoSet(r)
        return FrozenIsoView(r)
    
    def __xor__(self, other : Set[K]) -> "FrozenIsoView[K]":
        if not isinstance(other, FrozenIsoView.__Set):
            return NotImplemented
        return FrozenIsoView(self.__set ^ other)
    
    def __rxor__(self, other : Set[K]) -> "FrozenIsoView[K]":
        if not isinstance(other, FrozenIsoView.__Set):
            return NotImplemented
        r = other ^ self.__set
        if not isinstance(r, FrozenIsoSet):
            r = FrozenIsoSet(r)
        return FrozenIsoView(r)





V = TypeVar("V")

class IsoDictKeys(KeysView[K], Generic[K, V]):

    """
    This is the equivalent class of dict_keys that list keys of IsoDicts.
    Note that they behave like IsoViews:

    >>> a = 371643175454
    >>> b = a + 1 - 1
    >>> a is b              # For large integers, CPython creates new objects for each result.
    False
    >>> a + 1 - 1 in IsoDict(((a, 1), (b, 2), (3, 3), (3, 4)))
    False
    >>> a + 1 - 1 in IsoDict(((a, 1), (b, 2), (3, 3), (3, 4))).keys()
    True

    These equality checks are performed for all comparisons (calling '__eq__' on elements for operators 'in', ==, !=, <, <=, >, >=).
    Note that these comparisons fall back to regular comparisons when one of the operands is not an IsoDictKeys.
    """

    from collections.abc import Set as __Set, Hashable as __Hashable

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
        if self is value:
            return True
        if not isinstance(value, IsoDictKeys.__Set):
            return False
        if not isinstance(value, IsoDictKeys):
            return NotImplemented
        if len(self.__mapping) != len(value.__mapping):
            return False
        for h, self_hdict in self.__table.items():
            value_hdict : "dict[int, tuple[K, V]]" = value.__table.get(h, {})
            value_hdict, self_hdict = {i : k for i, k in value_hdict.items() if i not in self_hdict}, {i : k for i, k in self_hdict.items() if i not in value_hdict}    # Skipping identical elements
            if len(self_hdict) != len(value_hdict):
                return False
            while self_hdict:
                ia, (a, va) = self_hdict.popitem()
                for ib, (b, vb) in value_hdict.items():
                    if a == b:
                        value_hdict.pop(ib)
                        break
                else:
                    return False
        return True
    
    def __le__(self, other: Set[Any]) -> bool:
        if self is other:
            return True
        if not isinstance(other, IsoDictKeys.__Set):
            raise TypeError(f"'<=' not supported between instances of '{type(self).__name__}' and '{type(other).__name__}'")
        if not isinstance(other, IsoDictKeys):
            return NotImplemented
        if len(self.__mapping) > len(other.__mapping):
            return False
        for h, self_hdict in self.__table.items():
            other_hdict : "dict[int, tuple[K, V]]" = other.__table.get(h, {})
            other_hdict, self_hdict = {i : k for i, k in other_hdict.items() if i not in self_hdict}, {i : k for i, k in self_hdict.items() if i not in other_hdict}    # Skipping identical elements
            if len(self_hdict) > len(other_hdict):
                return False
            while self_hdict:
                ia, (a, va) = self_hdict.popitem()
                for ib, (b, vb) in other_hdict.items():
                    if a == b:
                        other_hdict.pop(ib)
                        break
                else:
                    return False
        return True
    
    def __lt__(self, other: Set[Any]) -> bool:
        if self is other:
            return False
        if not isinstance(other, IsoDictKeys.__Set):
            raise TypeError(f"'<' not supported between instances of '{type(self).__name__}' and '{type(other).__name__}'")
        if not isinstance(other, IsoDictKeys):
            return NotImplemented
        if len(self.__mapping) >= len(other.__mapping):
            return False
        for h, self_hdict in self.__table.items():
            other_hdict : "dict[int, tuple[K, V]]" = other.__table.get(h, {})
            other_hdict, self_hdict = {i : k for i, k in other_hdict.items() if i not in self_hdict}, {i : k for i, k in self_hdict.items() if i not in other_hdict}    # Skipping identical elements
            if len(self_hdict) > len(other_hdict):
                return False
            while self_hdict:
                ia, (a, va) = self_hdict.popitem()
                for ib, (b, vb) in other_hdict.items():
                    if a == b:
                        other_hdict.pop(ib)
                        break
                else:
                    return False
        return True
    
    def __ge__(self, other: Set[Any]) -> bool:
        if self is other:
            return True
        if not isinstance(other, IsoDictKeys.__Set):
            raise TypeError(f"'>=' not supported between instances of '{type(self).__name__}' and '{type(other).__name__}'")
        if not isinstance(other, IsoDictKeys):
            return NotImplemented
        if len(self.__mapping) < len(other.__mapping):
            return False
        for h, self_hdict in self.__table.items():
            other_hdict : "dict[int, tuple[K, V]]" = other.__table.get(h, {})
            other_hdict, self_hdict = {i : k for i, k in other_hdict.items() if i not in self_hdict}, {i : k for i, k in self_hdict.items() if i not in other_hdict}    # Skipping identical elements
            if len(self_hdict) < len(other_hdict):
                return False
            while other_hdict:
                ia, (a, va) = other_hdict.popitem()
                for ib, (b, vb) in self_hdict.items():
                    if a == b:
                        self_hdict.pop(ib)
                        break
                else:
                    return False
        return True
    
    def __gt__(self, other: Set[Any]) -> bool:
        if self is other:
            return False
        if not isinstance(other, IsoDictKeys.__Set):
            raise TypeError(f"'>' not supported between instances of '{type(self).__name__}' and '{type(other).__name__}'")
        if not isinstance(other, IsoDictKeys):
            return NotImplemented
        if len(self.__mapping) <= len(other.__mapping):
            return False
        for h, self_hdict in self.__table.items():
            other_hdict : "dict[int, tuple[K, V]]" = other.__table.get(h, {})
            other_hdict, self_hdict = {i : k for i, k in other_hdict.items() if i not in self_hdict}, {i : k for i, k in self_hdict.items() if i not in other_hdict}    # Skipping identical elements
            if len(self_hdict) < len(other_hdict):
                return False
            while other_hdict:
                ia, (a, va) = other_hdict.popitem()
                for ib, (b, vb) in self_hdict.items():
                    if a == b:
                        self_hdict.pop(ib)
                        break
                else:
                    return False
        return True
    
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

    from collections.abc import ValuesView as __ValuesView

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

    from collections.abc import Set as __Set, Hashable as __Hashable

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
        if not isinstance(value, IsoDictItems.__Set):
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
    The isomorphic dict is a container similar to dict except that it can contain keys that can be equal as long as they are not the same objects in memory (a is not b but a == b).
    As such searching, adding or removing a key is based on identity (using builtin function id()).

    >>> a = 371643175454
    >>> b = a + 1 - 1
    >>> a is b              # For large integers, CPython creates new objects for each result.
    False
    >>> IsoDict(((a, 1), (b, 2), (3, 3), (3, 4)))
    IsoDict([(371643175454, 1), (371643175454, 2), (3, 4)])
    >>> a + 1 - 1 in IsoDict(((a, 1), (b, 2), (3, 3), (3, 4)))
    False
    >>> a in IsoDict(((a, 1), (b, 2), (3, 3), (3, 4)))
    True

    Use IsoDict.keys() to manipulate keys based on equality.
    """

    from collections.abc import Iterable as __Iterable, Hashable as __Hashable, Mapping as __Mapping
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
    
    def __reduce__(self):
        return IsoDict, (), None, None, iter(self.items())

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
        if self is value:
            return True
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
    




class FrozenIsoDict(IsoDict[K, V]):

    """
    Frozen (immutable) version of IsoDicts.
    """

    __slots__ = {
        "__hash" : "The hash of the FrozenIsoDict"
    }

    def __reduce__(self):
        return FrozenIsoDict, (IsoDict(self), )

    def __delitem__(self, v : V):
        raise TypeError("'FrozenIsoDict' object doesn't support item deletion")

    def __ior__(self, __value : Mapping[K, V]):
        return NotImplemented

    def __setitem__(self, k : K, v : V):
        raise TypeError("'FrozenIsoDict' object does not support item assignment")

    def clear(self):
        raise AttributeError("'FrozenIsoDict' object has no attribute 'clear'")

    def copy(self):
        return FrozenIsoDict(self)
    
    def pop(self, k : K) -> V:
        raise AttributeError("'FrozenIsoDict' object has no attribute 'pop'")
    
    def popitem(self) -> tuple[K, V]:
        raise AttributeError("'FrozenIsoDict' object has no attribute 'popitem'")
    
    def setdefault(self, __key : K, __default : V):
        raise AttributeError("'FrozenIsoDict' object has no attribute 'setdefault'")
    
    def update(self, iterable : Mapping[K, V]):
        raise AttributeError("'FrozenIsoDict' object has no attribute 'update'")
    
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
    
    def __or__(self, __value: Mapping[K, V]) -> "FrozenIsoDict[K, V]":
        return FrozenIsoDict(super().__or__(__value))
    
    def __ror__(self, __value: Mapping[K, V]) -> "FrozenIsoDict[K, V]":
        return FrozenIsoDict(super().__ror__(__value))
    
    @staticmethod
    def fromkeys(iterable : Iterable[K], value : V | None = None) -> "FrozenIsoDict[K, V | None]":
        return FrozenIsoDict(super().fromkeys(iterable, value))





del K, V, ItemsView, MutableSet, KeysView, MutableMapping, ValuesView, Set, Any, Generic, Iterable, Iterator, Mapping, TypeVar, Hashable, overload