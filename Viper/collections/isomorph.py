"""
This module defines collections which are like sets and dict but they allow for repetition and have advance lookup methods.

Note that to work, these collections assume that elements are not equal if their hashes are different and that equality is transitive.
"""

from collections.abc import ItemsView, Iterator, MutableSet, KeysView, Mapping, MutableMapping, ValuesView, Set, Hashable, Iterable
from typing import Any, Generic, Iterator, TypeVar, overload

__all__ = ["IsoSet", "FrozenIsoSet", "IsoDict", "FrozenIsoDict"]





K1 = TypeVar("K1", bound=Hashable)
K2 = TypeVar("K2", bound=Hashable)

class IsoSet(MutableSet[K1]):

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

    def __init__(self, iterable : Iterable[K1] = ()) -> None:
        if not isinstance(iterable, IsoSet.__Iterable):
            raise TypeError(f"Expected iterable, got '{type(iterable).__name__}'")
        
        self.__table : "dict[int, dict[int, K1]]" = {}
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
        self.__table : "dict[int, dict[int, K1]]" = {}
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
    def iso_view(self) -> "IsoView[K1]":
        """
        An IsoView of the set. It behaves like the IsoSet except set operations are based on equality.
        """
        return IsoView(self)
    
    def __iter__(self) -> Iterator[K1]:
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
    
    def add(self, value: K1) -> None:
        if not isinstance(value, IsoSet.__Hashable):
            raise TypeError(f"unhashable type: '{type(value).__name__}'")
        if value in self:
            return
        self.__table.setdefault(hash(value), {})[id(value)] = value
        self.__len += 1

    def clear(self) -> None:
        self.__table.clear()
        self.__len = 0

    def copy(self) -> "IsoSet[K1]":
        """
        Return a shallow copy of an IsoSet.
        """
        cp = IsoSet()
        cp.__table = {h : hdict.copy() for h, hdict in self.__table.items()}
        cp.__len = self.__len
        return cp
        
    def difference(self, *sets : Iterable[K2]) -> "IsoSet[K1]":
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
    
    def difference_update(self, *sets : Iterable[K1]):
        """
        Remove all elements of another set from this IsoSet.
        """
        for si in sets:
            if not isinstance(si, IsoSet.__Iterable):
                raise TypeError(f"Expected iterable, got '{type(si).__name__}'")
        for si in sets:
            for k in si:
                self.discard(k)
    
    def discard(self, value: K1 | K2) -> None:
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

    def intersection(self, *sets : Iterable[K2]) -> "IsoSet[K1]":
        """
        Return the difference of two or more sets as a new IsoSet.

        (i.e. all elements that are in this set but not the others.)
        """
        for si in sets:
            if not isinstance(si, IsoSet.__Iterable):
                raise TypeError(f"Expected iterable, got '{type(si).__name__}'")
        return self.difference(self.difference(*sets))
    
    def intersection_update(self, *sets : Iterable[K1]):
        """
        Update an IsoSet with the intersection of itself and another.
        """
        for si in sets:
            if not isinstance(si, IsoSet.__Iterable):
                raise TypeError(f"Expected iterable, got '{type(si).__name__}'")
        self.difference_update(self.difference(*sets))
    
    def isdisjoint(self, s : Iterable[K1]) -> bool:
        """
        Return True if two sets have a null intersection.
        """
        if not isinstance(s, IsoSet.__Iterable):
            raise TypeError(f"Expected iterable, got '{type(s).__name__}'")
        return all(k not in self for k in s)
    
    def issubset(self, s : Iterable[K1]) -> bool:
        """
        Report whether another set contains this IsoSet.
        """
        if not isinstance(s, IsoSet.__Iterable):
            raise TypeError(f"Expected iterable, got '{type(s).__name__}'")
        s = IsoSet(s)
        return all(k in s for k in self)
    
    def issuperset(self, s : Iterable[K1]) -> bool:
        """
        Report whether this IsoSet contains another set.
        """
        if not isinstance(s, IsoSet.__Iterable):
            raise TypeError(f"Expected iterable, got '{type(s).__name__}'")
        return all(k in self for k in s)
    
    def pop(self) -> K1:
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
        self.__len -= 1
        return e
        
    def remove(self, e : K1):
        """
        Remove an element from an IsoSet; it must be a member.

        If the element is not a member, raise a KeyError.
        """
        if e in self:
            self.discard(e)
        else:
            raise KeyError(repr(e))
    
    def symmetric_difference(self, s : Iterable[K2]) -> "IsoSet[K1 | K2]":
        """
        Return the symmetric difference of two sets as a new set.

        (i.e. all elements that are in exactly one of the sets.)
        """
        if not isinstance(s, IsoSet.__Iterable):
            raise TypeError(f"Expected iterable, got '{type(s).__name__}'")
        res : "IsoSet[K1 | K2]" = self.copy() # type: ignore
        for k in s:
            if k in res:
                res.remove(k)
            else:
                res.add(k)
        return res
    
    def symmetric_difference_update(self, s : Iterable[K1]):
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

    def union(self, *sets : Iterable[K2]) -> "IsoSet[K1 | K2]":
        """
        Return the union of sets as a new set.

        (i.e. all elements that are in either set.)
        """
        s : "IsoSet[K1 | K2]" = self.copy() # type: ignore
        for si in sets:
            if not isinstance(si, IsoSet.__Iterable):
                raise TypeError(f"Expected iterable, got '{type(si).__name__}'")
        for si in sets:
            for k in si:
                s.add(k)
        return s
    
    def update(self, *sets : Iterable[K1]):
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
    
    def __and__(self, other : Set[K2]) -> "IsoSet[K1]":
        if not isinstance(other, IsoSet.__Set):
            return NotImplemented
        return IsoSet(k for k in self if k in other)
    
    def __rand__(self, other : Set[K2]) -> "IsoSet[K2]":
        if not isinstance(other, IsoSet.__Set):
            return NotImplemented
        return IsoSet(k for k in other if k in self)
        
    def __iand__(self, other : Set[K1]) -> "IsoSet[K1]":
        if not isinstance(other, IsoSet.__Set):
            return NotImplemented
        for k in self.copy():
            if k not in other:
                self.remove(k)
        return self
    
    def __or__(self, other : Set[K2]) -> "IsoSet[K1 | K2]":
        if not isinstance(other, IsoSet.__Set):
            return NotImplemented
        s : "IsoSet[K1 | K2]" = IsoSet(self)
        for k in other:
            s.add(k)
        return s
    
    def __ror__(self, other : Set[K2]) -> "IsoSet[K1 | K2]":
        if not isinstance(other, IsoSet.__Set):
            return NotImplemented
        s : "IsoSet[K1 | K2]" = IsoSet(self)
        for k in other:
            s.add(k)
        return s
    
    def __ior__(self, other : Set[K1]) -> "IsoSet[K1]":
        if not isinstance(other, IsoSet.__Set):
            return NotImplemented
        for k in other:
            self.add(k)
        return self
    
    def __sub__(self, other : Set[K2]) -> "IsoSet[K1]":
        if not isinstance(other, IsoSet.__Set):
            return NotImplemented
        return IsoSet(k for k in self if k not in other)
    
    def __rsub__(self, other : Set[K2]) -> "IsoSet[K2]":
        if not isinstance(other, IsoSet.__Set):
            return NotImplemented
        return IsoSet(k for k in other if k not in self)
    
    def __isub__(self, other : Set[K1]) -> "IsoSet[K1]":
        if not isinstance(other, IsoSet.__Set):
            return NotImplemented
        for k in other:
            self.discard(k)
        return self
    
    def __xor__(self, other : Set[K2]) -> "IsoSet[K1 | K2]":
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
    
    def __rxor__(self, other : Set[K2]) -> "IsoSet[K1 | K2]":
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
    
    def __ixor__(self, other : Set[K1]) -> "IsoSet[K1]":
        if not isinstance(other, IsoSet.__Set):
            return NotImplemented
        for k in other:
            if k in self:
                self.remove(k)
            else:
                self.add(k)
        return self
    
    def __matmul__(self, other : "IsoSet[K2] | IsoView[K2] | FrozenIsoSet[K2] | FrozenIsoView[K2]") -> "IsoMappings[K1, K2]":
        """
        Implements self @ other. Returns the IsoMappings between two IsoViews
        """
        if not isinstance(other, IsoSet | IsoView | FrozenIsoSet | FrozenIsoView):
            return NotImplemented
        if isinstance(other, IsoSet | FrozenIsoSet):
            other = other.iso_view
        return IsoView.compare(self.iso_view, other)
    




class FrozenIsoSet(Set[K1]):

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

    def __init__(self, iterable : Iterable[K1] = ()) -> None:
        if not isinstance(iterable, FrozenIsoSet.__Iterable):
            raise TypeError(f"Expected iterable, got '{type(iterable).__name__}'")
        
        self.__table : "dict[int, dict[int, K1]]" = {}
        for t in iterable:
            if not isinstance(t, FrozenIsoSet.__Hashable):
                raise TypeError(f"unhashable type: '{type(t).__name__}'")
            self.__table.setdefault(hash(t), {})[id(t)] = t
        self.__len = sum(len(hdict) for hdict in self.__table.values())
        self.__hash : int | None = None

    def __getstate__(self):
        return {"data" : list(self)}

    def __setstate__(self, state):
        self.__table : "dict[int, dict[int, K1]]" = {}
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
    def iso_view(self) -> "FrozenIsoView[K1]":
        """
        An IsoView of the set. It behaves like the FrozenIsoSet except set operations are based on equality.
        """
        return FrozenIsoView(self)
    
    def __iter__(self) -> Iterator[K1]:
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
    
    def copy(self) -> "FrozenIsoSet[K1]":
        """
        Return a shallow copy of an FrozenIsoSet.
        """
        cp = FrozenIsoSet()
        cp.__table = {h : hdict.copy() for h, hdict in self.__table.items()}
        cp.__len = self.__len
        return cp
        
    def difference(self, *sets : Iterable[K2]) -> "FrozenIsoSet[K1]":
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
    
    def intersection(self, *sets : Iterable[K2]) -> "FrozenIsoSet[K1]":
        """
        Return the difference of two or more sets as a new FrozenIsoSet.

        (i.e. all elements that are in this set but not the others.)
        """
        for si in sets:
            if not isinstance(si, FrozenIsoSet.__Iterable):
                raise TypeError(f"Expected iterable, got '{type(si).__name__}'")
        return self.difference(self.difference(*sets))
    
    def isdisjoint(self, s : Iterable[K1]) -> bool:
        """
        Return True if two sets have a null intersection.
        """
        if not isinstance(s, FrozenIsoSet.__Iterable):
            raise TypeError(f"Expected iterable, got '{type(s).__name__}'")
        return all(k not in self for k in s)
    
    def issubset(self, s : Iterable[K1]) -> bool:
        """
        Report whether another set contains this FrozenIsoSet.
        """
        if not isinstance(s, FrozenIsoSet.__Iterable):
            raise TypeError(f"Expected iterable, got '{type(s).__name__}'")
        s = FrozenIsoSet(s)
        return all(k in s for k in self)
    
    def issuperset(self, s : Iterable[K1]) -> bool:
        """
        Report whether this FrozenIsoSet contains another set.
        """
        if not isinstance(s, FrozenIsoSet.__Iterable):
            raise TypeError(f"Expected iterable, got '{type(s).__name__}'")
        return all(k in self for k in s)
    
    def symmetric_difference(self, s : Iterable[K2]) -> "FrozenIsoSet[K1 | K2]":
        """
        Return the symmetric difference of two sets as a new set.

        (i.e. all elements that are in exactly one of the sets.)
        """
        if not isinstance(s, FrozenIsoSet.__Iterable):
            raise TypeError(f"Expected iterable, got '{type(s).__name__}'")
        res : "FrozenIsoSet[K1 | K2]" = self.copy() # type: ignore
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

    def union(self, *sets : Iterable[K2]) -> "FrozenIsoSet[K1 | K2]":
        """
        Return the union of sets as a new set.

        (i.e. all elements that are in either set.)
        """
        s : "FrozenIsoSet[K1 | K2]" = self.copy() # type: ignore
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
    
    def __and__(self, other : Set[K2]) -> "FrozenIsoSet[K1]":
        if not isinstance(other, FrozenIsoSet.__Set):
            return NotImplemented
        return FrozenIsoSet(k for k in self if k in other)
    
    def __rand__(self, other : Set[K2]) -> "FrozenIsoSet[K2]":
        if not isinstance(other, FrozenIsoSet.__Set):
            return NotImplemented
        return FrozenIsoSet(k for k in other if k in self)
            
    def __or__(self, other : Set[K2]) -> "FrozenIsoSet[K1 | K2]":
        if not isinstance(other, FrozenIsoSet.__Set):
            return NotImplemented
        s : "FrozenIsoSet[K1 | K2]" = FrozenIsoSet(self)
        for k in other:
            if k not in s:
                s.__table.setdefault(hash(k), {})[id(k)] = k
                s.__len += 1
        return s
    
    def __ror__(self, other : Set[K2]) -> "FrozenIsoSet[K1 | K2]":
        if not isinstance(other, FrozenIsoSet.__Set):
            return NotImplemented
        s : "FrozenIsoSet[K1 | K2]" = FrozenIsoSet(self)
        for k in other:
            if k not in s:
                s.__table.setdefault(hash(k), {})[id(k)] = k
                s.__len += 1
        return s
        
    def __sub__(self, other : Set[K2]) -> "FrozenIsoSet[K1]":
        if not isinstance(other, FrozenIsoSet.__Set):
            return NotImplemented
        return FrozenIsoSet(k for k in self if k not in other)
    
    def __rsub__(self, other : Set[K2]) -> "FrozenIsoSet[K2]":
        if not isinstance(other, FrozenIsoSet.__Set):
            return NotImplemented
        return FrozenIsoSet(k for k in other if k not in self)
    
    def __xor__(self, other : Set[K2]) -> "FrozenIsoSet[K1 | K2]":
        if not isinstance(other, FrozenIsoSet.__Set):
            return NotImplemented
        s = FrozenIsoSet()
        for k in self:
            if k not in other:
                s.__table.setdefault(hash(k), {})[id(k)] = k
                s.__len += 1
        for k in other:
            if k not in self:
                s.__table.setdefault(hash(k), {})[id(k)] = k
                s.__len += 1
        return s
    
    def __rxor__(self, other : Set[K2]) -> "FrozenIsoSet[K1 | K2]":
        if not isinstance(other, FrozenIsoSet.__Set):
            return NotImplemented
        s = FrozenIsoSet()
        for k in self:
            if k not in other:
                s.__table.setdefault(hash(k), {})[id(k)] = k
                s.__len += 1
        for k in other:
            if k not in self:
                s.__table.setdefault(hash(k), {})[id(k)] = k
                s.__len += 1
        return s
    
    def __matmul__(self, other : "IsoSet[K2] | IsoView[K2] | FrozenIsoSet[K2] | FrozenIsoView[K2]") -> "IsoMappings[K1, K2]":
        """
        Implements self @ other. Returns the IsoMappings between two IsoViews
        """
        if not isinstance(other, IsoSet | IsoView | FrozenIsoSet | FrozenIsoView):
            return NotImplemented
        if isinstance(other, IsoSet | FrozenIsoSet):
            other = other.iso_view
        return IsoView.compare(self.iso_view, other)
    




class IsoView(MutableSet[K1]):

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

    def __init__(self, isoset : IsoSet[K1]) -> None:
        self.__set = isoset
        self.__table : "dict[int, dict[int, K1]]" = isoset._IsoSet__table # type: ignore

    @property
    def set(self) -> IsoSet[K1]:
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
    
    def __iter__(self) -> Iterator[K1]:
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
    
    @staticmethod
    def __get_frozen_table(s : "FrozenIsoView[K1]") -> dict[int, dict[int, K1]]:
        """
        Internal function used to extract the hash map of a FrozenIsoView.
        """
        return s._FrozenIsoView__table # type: ignore
    
    @staticmethod
    def compare(s1 : "IsoView[K1] | FrozenIsoView[K1]", s2 : "IsoView[K2] | FrozenIsoView[K2]") -> "IsoMappings[K1, K2]":
        """
        Returns an object that represents all the possible isomorphic mappings between the two given IsoViews.
        """
        if not isinstance(s1, IsoView | FrozenIsoView) or not isinstance(s2, IsoView | FrozenIsoView):
            raise TypeError(f"Expected two IsoViews or FrozenIsoViews, got '{type(s1).__name__}' and '{type(s2).__name__}'")
        if isinstance(s1, IsoView):
            t1 = s1.__table
        else:
            t1 = IsoView.__get_frozen_table(s1)
        if isinstance(s2, IsoView):
            t2 = s2.__table
        else:
            t2 = IsoView.__get_frozen_table(s2)
        return IsoMappings(t1, t2, s1, s2)
    
    def add(self, value: K1) -> None:
        if not isinstance(value, IsoView.__Hashable):
            raise TypeError(f"unhashable type: '{type(value).__name__}'")
        h = hash(value)
        if h not in self.__table or (id(value) not in self.__table[h] and not any(x == value for x in self.__table[h].values())):
            self.__set.add(value)

    def clear(self) -> None:
        self.__set.clear()

    def copy(self) -> "IsoView[K1]":
        """
        Return a shallow copy of an IsoView.
        """
        return IsoView(self.__set.copy())
        
    def difference(self, *sets : Iterable[K2]) -> "IsoView[K1]":
        """
        Return the difference of two or more sets as a new IsoView.

        (i.e. all elements that are in this set but cannot be mapped to any in the others.)
        """
        for si in sets:
            if not isinstance(si, IsoView.__Iterable):
                raise TypeError(f"Expected iterable, got '{type(si).__name__}'")
        s = self.copy()
        for si in sets:
            if not isinstance(si, IsoSet | IsoView | FrozenIsoSet | FrozenIsoView):
                si = IsoSet(si)
            if not isinstance(si, IsoView | FrozenIsoView):
                si = si.iso_view
            comp = IsoView.compare(s, si)
            if comp:
                for k in tuple(next(iter(comp))):  # Avoid mapped set's size chaging during iteration
                    s.remove(k)
        return s
    
    def difference_update(self, *sets : Iterable[K1]):
        """
        Remove all elements from this IsoView that can be mapped to any of the other sets.
        """
        for si in sets:
            if not isinstance(si, IsoView.__Iterable):
                raise TypeError(f"Expected iterable, got '{type(si).__name__}'")
        for si in sets:
            if not isinstance(si, IsoSet | IsoView | FrozenIsoSet | FrozenIsoView):
                si = IsoSet(si)
            if not isinstance(si, IsoView | FrozenIsoView):
                si = si.iso_view
            comp = IsoView.compare(self, si)
            if comp:
                for k in tuple(next(iter(comp))):  # Avoid mapped set's size chaging during iteration
                    self.remove(k)
    
    def discard(self, value : K1 | K2) -> None:
        if not isinstance(value, IsoView.__Hashable):
            raise TypeError(f"unhashable type: '{type(value).__name__}'")
        h = hash(value)
        if h in self.__table:
            if value in self.__set:
                self.__set.remove(value)
            else:
                for x in self.__table[h].values():
                    if x == value:
                        self.__set.remove(x)
                        return

    def intersection(self, *sets : Iterable[K2]) -> "IsoView[K1]":
        """
        Return the intersection of two or more sets as a new IsoView.

        (i.e. all elements that are in this set that can be mapped to elements in all of the others.)
        """
        for si in sets:
            if not isinstance(si, IsoView.__Iterable):
                raise TypeError(f"Expected iterable, got '{type(si).__name__}'")
        s = self.copy()
        for si in sets:
            if not isinstance(si, IsoSet | IsoView | FrozenIsoSet | FrozenIsoView):
                si = IsoSet(si)
            if not isinstance(si, IsoView | FrozenIsoView):
                si = si.iso_view
            comp = IsoView.compare(s, si)
            if comp:
                si = next(iter(comp))
                s.difference_update(k for k in s if k not in si)
        return s
    
    def intersection_update(self, *sets : Iterable[K1]):
        """
        Update an IsoView with the intersection of itself and another.
        """
        for si in sets:
            if not isinstance(si, IsoView.__Iterable):
                raise TypeError(f"Expected iterable, got '{type(si).__name__}'")
        for si in sets:
            if not isinstance(si, IsoSet | IsoView | FrozenIsoSet | FrozenIsoView):
                si = IsoSet(si)
            if not isinstance(si, IsoView | FrozenIsoView):
                si = si.iso_view
            comp = IsoView.compare(self, si)
            if comp:
                si = next(iter(comp))
                self.difference_update(k for k in self if k not in si)
    
    def isdisjoint(self, s : Iterable[K1]) -> bool:
        """
        Return True if two IsoView have no elements that can be mapped together.
        """
        if not isinstance(s, IsoView.__Iterable):
            raise TypeError(f"Expected iterable, got '{type(s).__name__}'")
        if not isinstance(s, IsoSet | IsoView | FrozenIsoSet | FrozenIsoView):
            s = IsoSet(s)
        if not isinstance(s, IsoView | FrozenIsoView):
            s = s.iso_view
        comp = IsoView.compare(self, s)
        return not bool(comp)
    
    def issubset(self, s : Iterable[K1]) -> bool:
        """
        Report whether all elements of this IsoView can be mapped to elements of another.
        """
        if not isinstance(s, IsoView.__Iterable):
            raise TypeError(f"Expected iterable, got '{type(s).__name__}'")
        if not isinstance(s, IsoSet | IsoView | FrozenIsoSet | FrozenIsoView):
            s = IsoSet(s)
        if not isinstance(s, IsoView | FrozenIsoView):
            s = s.iso_view
        comp = IsoView.compare(self, s)
        return comp.source_complete
    
    def issuperset(self, s : Iterable[K1]) -> bool:
        """
        Report whether all elements of another IsoView can be mapped to elements of this one.
        """
        if not isinstance(s, IsoView.__Iterable):
            raise TypeError(f"Expected iterable, got '{type(s).__name__}'")
        if not isinstance(s, IsoSet | IsoView | FrozenIsoSet | FrozenIsoView):
            s = IsoSet(s)
        if not isinstance(s, IsoView | FrozenIsoView):
            s = s.iso_view
        comp = IsoView.compare(self, s)
        return comp.destination_complete
    
    def pop(self) -> K1:
        """
        Remove and return an arbitrary IsoView element.
        Raises KeyError if the IsoView is empty.
        """
        if not self:
            raise KeyError("'pop from empty IsoView'")
        return self.__set.pop()
        
    def remove(self, e : K1):
        """
        Remove an element from an IsoView; it must have an equal member.

        If no equal element is found, raise a KeyError.
        """
        if not isinstance(e, IsoView.__Hashable):
            raise TypeError(f"unhashable type: '{type(e).__name__}'")
        h = hash(e)
        if h in self.__table:
            if e in self.__set:
                self.__set.remove(e)
                return
            else:
                for x in self.__table[h].values():
                    if x == e:
                        self.__set.remove(x)
                        return
        raise KeyError(repr(e))
    
    def symmetric_difference(self, s : Iterable[K2]) -> "IsoView[K1 | K2]":
        """
        Return the symmetric difference of two sets as a new IsoView.

        (i.e. all elements that cannot be mapped between the two sets.)
        """
        if not isinstance(s, IsoView.__Iterable):
            raise TypeError(f"Expected iterable, got '{type(s).__name__}'")
        if not isinstance(s, IsoSet | IsoView | FrozenIsoSet | FrozenIsoView):
            s = IsoSet(s)
        if not isinstance(s, IsoView | FrozenIsoView):
            s = s.iso_view
        comp = IsoView.compare(self, s)
        if comp:
            si = next(iter(comp))
            si_inv = IsoSet(si.values())
            s2 = IsoSet(k for k in self if k not in si)
            return s2.union(k for k in s if k not in si_inv).iso_view
        return self.union(s)
    
    def symmetric_difference_update(self, s : Iterable[K1]):
        """
        Update an IsoView with the symmetric difference of itself and another.
        """
        if not isinstance(s, IsoView.__Iterable):
            raise TypeError(f"Expected iterable, got '{type(s).__name__}'")
        if not isinstance(s, IsoSet | IsoView | FrozenIsoSet | FrozenIsoView):
            s = IsoSet(s)
        if not isinstance(s, IsoView | FrozenIsoView):
            s = s.iso_view
        comp = IsoView.compare(self, s)
        if comp:
            si = next(iter(comp))
            si_inv = IsoSet(si.values())
            self.__set.difference_update(si)
            self.__set.update(k for k in s if k not in si_inv)
        else:
            self.__set.update(s)
        return self

    def union(self, *sets : Iterable[K2]) -> "IsoView[K1 | K2]":
        """
        Return the union of sets as a new IsoView.

        (i.e. all elements that are in either set but elements that can be mapped from one set to another will not be present twice.)
        """
        for si in sets:
            if not isinstance(si, IsoView.__Iterable):
                raise TypeError(f"Expected iterable, got '{type(si).__name__}'")
        s : "IsoView[K1 | K2]" = self.copy()
        for si in sets:
            if not isinstance(si, IsoSet | IsoView | FrozenIsoSet | FrozenIsoView):
                si = IsoSet(si)
            if not isinstance(si, IsoView | FrozenIsoView):
                si = si.iso_view
            comp = IsoView.compare(si, s)
            if comp:
                m = next(iter(comp))
                s.__set.update(k for k in si if k not in m)
            else:
                s.__set.update(si)
        return s
    
    def update(self, *sets : Iterable[K1]):
        """
        Update an IsoView with the union of itself and others.
        """
        for si in sets:
            if not isinstance(si, IsoView.__Iterable):
                raise TypeError(f"Expected iterable, got '{type(si).__name__}'")
        for si in sets:
            if not isinstance(si, IsoSet | IsoView | FrozenIsoSet | FrozenIsoView):
                si = IsoSet(si)
            if not isinstance(si, IsoView | FrozenIsoView):
                si = si.iso_view
            comp = IsoView.compare(si, self)
            if comp:
                m = next(iter(comp))
                self.__set.update(k for k in si if k not in m)
            else:
                self.__set.update(si)
    
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
        if not isinstance(value, IsoView | FrozenIsoView):
            return self.__set == value
        if len(self.__set) != len(value.set):
            return False
        comp = IsoView.compare(self, value)
        return comp.source_complete and comp.destination_complete
    
    def __le__(self, other: Set[Any]) -> bool:
        if self is other:
            return True
        if not isinstance(other, IsoView.__Set):
            raise TypeError(f"'<=' not supported between instances of '{type(self).__name__}' and '{type(other).__name__}'")
        if not isinstance(other, IsoView | FrozenIsoView):
            return self.__set <= other
        if len(self.__set) > len(other.set):
            return False
        comp = IsoView.compare(self, other)
        return comp.source_complete
    
    def __lt__(self, other: Set[Any]) -> bool:
        if self is other:
            return False
        if not isinstance(other, IsoView.__Set):
            raise TypeError(f"'<' not supported between instances of '{type(self).__name__}' and '{type(other).__name__}'")
        if not isinstance(other, IsoView | FrozenIsoView):
            return self.__set < other
        if len(self.__set) >= len(other.set):
            return False
        comp = IsoView.compare(self, other)
        return comp.source_complete and not comp.destination_complete
    
    def __ge__(self, other: Set[Any]) -> bool:
        if self is other:
            return True
        if not isinstance(other, IsoView.__Set):
            raise TypeError(f"'>=' not supported between instances of '{type(self).__name__}' and '{type(other).__name__}'")
        if not isinstance(other, IsoView | FrozenIsoView):
            return self.__set >= other
        if len(self.__set) < len(other.set):
            return False
        comp = IsoView.compare(self, other)
        return comp.destination_complete
    
    def __gt__(self, other: Set[Any]) -> bool:
        if self is other:
            return False
        if not isinstance(other, IsoView.__Set):
            raise TypeError(f"'>' not supported between instances of '{type(self).__name__}' and '{type(other).__name__}'")
        if not isinstance(other, IsoView | FrozenIsoView):
            return self.__set > other
        if len(self.__set) <= len(other.set):
            return False
        comp = IsoView.compare(self, other)
        return comp.destination_complete and not comp.source_complete
    
    def __and__(self, other : Set[K2]) -> "IsoView[K1]":
        if not isinstance(other, IsoView.__Set):
            return NotImplemented
        if isinstance(other, IsoView | FrozenIsoView):
            return self.intersection(other)
        return IsoView(self.__set & other)
    
    def __rand__(self, other : Set[K2]) -> "IsoView[K2]":
        if not isinstance(other, IsoView.__Set):
            return NotImplemented
        return IsoView(IsoSet(other & self.__set))
        
    def __iand__(self, other : Set[K1]) -> "IsoView[K1]":
        if not isinstance(other, IsoView.__Set):
            return NotImplemented
        if isinstance(other, IsoView | FrozenIsoView):
            self.intersection_update(other)
            return self
        self.__set &= other
        return self
    
    def __or__(self, other : Set[K2]) -> "IsoView[K1 | K2]":
        if not isinstance(other, IsoView.__Set):
            return NotImplemented
        if isinstance(other, IsoView | FrozenIsoView):
            return self.union(other)
        return IsoView(IsoSet(other & self.__set))
    
    def __ror__(self, other : Set[K2]) -> "IsoView[K1 | K2]":
        if not isinstance(other, IsoView.__Set):
            return NotImplemented
        return IsoView(IsoSet(other | self.__set))
    
    def __ior__(self, other : Set[K1]) -> "IsoView[K1]":
        if not isinstance(other, IsoView.__Set):
            return NotImplemented
        if isinstance(other, IsoView | FrozenIsoView):
            self.update(other)
            return self
        self.__set |= other
        return self
    
    def __sub__(self, other : Set[K2]) -> "IsoView[K1]":
        if not isinstance(other, IsoView.__Set):
            return NotImplemented
        if isinstance(other, IsoView | FrozenIsoView):
            return self.difference(other)
        return IsoView(self.__set - other)
    
    def __rsub__(self, other : Set[K2]) -> "IsoView[K2]":
        if not isinstance(other, IsoView.__Set):
            return NotImplemented
        r = other - self.__set
        if not isinstance(r, IsoSet):
            r = IsoSet(r)
        return IsoView(r)
    
    def __isub__(self, other : Set[K1]) -> "IsoView[K1]":
        if not isinstance(other, IsoView.__Set):
            return NotImplemented
        if isinstance(other, IsoView | FrozenIsoView):
            self.difference_update(other)
            return self
        self.__set -= other
        return self
    
    def __xor__(self, other : Set[K2]) -> "IsoView[K1 | K2]":
        if not isinstance(other, IsoView.__Set):
            return NotImplemented
        if isinstance(other, IsoView | FrozenIsoView):
            return self.symmetric_difference(other)
        return IsoView(self.__set ^ other)
    
    def __rxor__(self, other : Set[K2]) -> "IsoView[K1 | K2]":
        if not isinstance(other, IsoView.__Set):
            return NotImplemented
        r = other ^ self.__set
        if not isinstance(r, IsoSet):
            r = IsoSet(r)
        return IsoView(r)
    
    def __ixor__(self, other : Set[K1]) -> "IsoView[K1]":
        if not isinstance(other, IsoView.__Set):
            return NotImplemented
        if isinstance(other, IsoView | FrozenIsoView):
            self.symmetric_difference_update(other)
            return self
        self.__set ^= other
        return self
    
    def __matmul__(self, other : "IsoSet[K2] | IsoView[K2] | FrozenIsoSet[K2] | FrozenIsoView[K2]") -> "IsoMappings[K1, K2]":
        """
        Implements self @ other. Returns the IsoMappings between two IsoViews.
        """
        if not isinstance(other, IsoSet | IsoView | FrozenIsoSet | FrozenIsoView):
            return NotImplemented
        if isinstance(other, IsoSet | FrozenIsoSet):
            other = other.iso_view
        return IsoView.compare(self, other)




class FrozenIsoView(Set[K1]):

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

    def __init__(self, isoset : FrozenIsoSet[K1]) -> None:
        self.__set = isoset
        self.__table : "dict[int, dict[int, K1]]" = isoset._FrozenIsoSet__table # type: ignore

    @property
    def set(self) -> FrozenIsoSet[K1]:
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
    
    def __iter__(self) -> Iterator[K1]:
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
    
    @staticmethod
    def __get_frozen_table(s : "IsoView[K1]") -> dict[int, dict[int, K1]]:
        """
        Internal function used to extract the hash map of an IsoView.
        """
        return s._IsoView__table # type: ignore
    
    @staticmethod
    def __freeze(s : "IsoView[K1]") -> "FrozenIsoView[K1]":
        """
        Internal function that transforms an IsoView into a FrozenIsoView without copies.
        """
        f = FrozenIsoView.__new__(FrozenIsoView)
        f.__set = FrozenIsoSet.__new__(FrozenIsoSet)
        f.__table = s._IsoView__table # type: ignore
        f.__set._FrozenIsoSet__table = f.__table # type: ignore
        f.__set._FrozenIsoSet__len = s.set._IsoSet__len # type: ignore
        return f
    
    @staticmethod
    def compare(s1 : "IsoView[K1] | FrozenIsoView[K1]", s2 : "IsoView[K2] | FrozenIsoView[K2]") -> "IsoMappings[K1, K2]":
        """
        Returns an object that represents all the possible isomorphic mappings between the two given IsoViews.
        """
        if not isinstance(s1, IsoView | FrozenIsoView) or not isinstance(s2, IsoView | FrozenIsoView):
            raise TypeError(f"Expected two IsoViews or FrozenIsoViews, got '{type(s1).__name__}' and '{type(s2).__name__}'")
        if isinstance(s1, FrozenIsoView):
            t1 = s1.__table
        else:
            t1 = FrozenIsoView.__get_frozen_table(s1)
        if isinstance(s2, FrozenIsoView):
            t2 = s2.__table
        else:
            t2 = FrozenIsoView.__get_frozen_table(s2)
        return IsoMappings(t1, t2, s1, s2)

    def copy(self) -> "FrozenIsoView[K1]":
        """
        Return a shallow copy of a FrozenIsoView.
        """
        return FrozenIsoView(self.__set.copy())
        
    def difference(self, *sets : Iterable[K2]) -> "FrozenIsoView[K1]":
        """
        Return the difference of two or more sets as a new FrozenIsoView.

        (i.e. all elements that are in this set but cannot be mapped to any in the others.)
        """
        for si in sets:
            if not isinstance(si, FrozenIsoView.__Iterable):
                raise TypeError(f"Expected iterable, got '{type(si).__name__}'")
        s = IsoSet(self.__set).iso_view
        for si in sets:
            if not isinstance(si, IsoSet | IsoView | FrozenIsoSet | FrozenIsoView):
                si = IsoSet(si)
            if not isinstance(si, IsoView | FrozenIsoView):
                si = si.iso_view
            comp = FrozenIsoView.compare(s, si)
            if comp:
                for k in tuple(next(iter(comp))):  # Avoid mapped set's size chaging during iteration
                    s.remove(k)
        return FrozenIsoView.__freeze(s)
    
    def intersection(self, *sets : Iterable[K2]) -> "FrozenIsoView[K1]":
        """
        Return the intersection of two or more sets as a new FrozenIsoView.

        (i.e. all elements that are in this set that can be mapped to elements in all of the others.)
        """
        for si in sets:
            if not isinstance(si, FrozenIsoView.__Iterable):
                raise TypeError(f"Expected iterable, got '{type(si).__name__}'")
        s = IsoSet(self.__set).iso_view
        for si in sets:
            if not isinstance(si, IsoSet | IsoView | FrozenIsoSet | FrozenIsoView):
                si = IsoSet(si)
            if not isinstance(si, IsoView | FrozenIsoView):
                si = si.iso_view
            comp = FrozenIsoView.compare(s, si)
            if comp:
                si = next(iter(comp))
                s.difference_update(k for k in s if k not in si)
        return FrozenIsoView.__freeze(s)
    
    def isdisjoint(self, s : Iterable[K1]) -> bool:
        """
        Return True if two FrozenIsoView have no elements that can be mapped together.
        """
        if not isinstance(s, FrozenIsoView.__Iterable):
            raise TypeError(f"Expected iterable, got '{type(s).__name__}'")
        if not isinstance(s, IsoSet | IsoView | FrozenIsoSet | FrozenIsoView):
            s = IsoSet(s)
        if not isinstance(s, IsoView | FrozenIsoView):
            s = s.iso_view
        comp = FrozenIsoView.compare(self, s)
        return not bool(comp)
    
    def issubset(self, s : Iterable[K1]) -> bool:
        """
        Report whether all elements of this FrozenIsoView can be mapped to elements of another.
        """
        if not isinstance(s, FrozenIsoView.__Iterable):
            raise TypeError(f"Expected iterable, got '{type(s).__name__}'")
        if not isinstance(s, IsoSet | IsoView | FrozenIsoSet | FrozenIsoView):
            s = IsoSet(s)
        if not isinstance(s, IsoView | FrozenIsoView):
            s = s.iso_view
        comp = FrozenIsoView.compare(self, s)
        return comp.source_complete
    
    def issuperset(self, s : Iterable[K1]) -> bool:
        """
        Report whether all elements of another FrozenIsoView can be mapped to elements of this one.
        """
        if not isinstance(s, FrozenIsoView.__Iterable):
            raise TypeError(f"Expected iterable, got '{type(s).__name__}'")
        if not isinstance(s, IsoSet | IsoView | FrozenIsoSet | FrozenIsoView):
            s = IsoSet(s)
        if not isinstance(s, IsoView | FrozenIsoView):
            s = s.iso_view
        comp = FrozenIsoView.compare(self, s)
        return comp.destination_complete
    
    def symmetric_difference(self, s : Iterable[K2]) -> "FrozenIsoView[K1 | K2]":
        """
        Return the symmetric difference of two sets as a new FrozenIsoView.

        (i.e. all elements that cannot be mapped between the two sets.)
        """
        if not isinstance(s, FrozenIsoView.__Iterable):
            raise TypeError(f"Expected iterable, got '{type(s).__name__}'")
        if not isinstance(s, IsoSet | IsoView | FrozenIsoSet | FrozenIsoView):
            s = IsoSet(s)
        if not isinstance(s, IsoView | FrozenIsoView):
            s = s.iso_view
        comp = FrozenIsoView.compare(self, s)
        if comp:
            si = next(iter(comp))
            si_inv = IsoSet(si.values())
            s2 = IsoSet(k for k in self if k not in si)
            return FrozenIsoView.__freeze(s2.union(k for k in s if k not in si_inv).iso_view)
        return self.union(s)

    def union(self, *sets : Iterable[K2]) -> "FrozenIsoView[K1 | K2]":
        """
        Return the union of sets as a new FrozenIsoView.

        (i.e. all elements that are in either set but elements that can be mapped from one set to another will not be present twice.)
        """
        for si in sets:
            if not isinstance(si, FrozenIsoView.__Iterable):
                raise TypeError(f"Expected iterable, got '{type(si).__name__}'")
        s : "IsoView[K1 | K2]" = IsoSet(self.__set).iso_view
        for si in sets:
            if not isinstance(si, IsoSet | IsoView | FrozenIsoSet | FrozenIsoView):
                si = IsoSet(si)
            if not isinstance(si, IsoView | FrozenIsoView):
                si = si.iso_view
            comp = FrozenIsoView.compare(si, s)
            if comp:
                m = next(iter(comp))
                s.set.update(k for k in si if k not in m)
            else:
                s.set.update(si)
        return FrozenIsoView.__freeze(s)
    
    def __sizeof__(self) -> int:
        return object.__sizeof__(self)
    
    def __getstate__(self) -> object:
        return {
            "__table" : self.__table,
            "__set" : self.__set,
            }

    @staticmethod
    def __from_view(v : IsoView[K1]) -> "FrozenIsoView[K1]":
        """
        Internal method used to avoid copying IsoView into FrozenIsoViews when comparing.
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
        if not isinstance(value, IsoView | FrozenIsoView):
            return self.__set == value
        if len(self.__set) != len(value.set):
            return False
        comp = FrozenIsoView.compare(self, value)
        return comp.source_complete and comp.destination_complete
    
    def __le__(self, other: Set[Any]) -> bool:
        if self is other:
            return True
        if not isinstance(other, FrozenIsoView.__Set):
            raise TypeError(f"'<=' not supported between instances of '{type(self).__name__}' and '{type(other).__name__}'")
        if not isinstance(other, IsoView | FrozenIsoView):
            return self.__set <= other
        if len(self.__set) > len(other.set):
            return False
        comp = FrozenIsoView.compare(self, other)
        return comp.source_complete
    
    def __lt__(self, other: Set[Any]) -> bool:
        if self is other:
            return False
        if not isinstance(other, FrozenIsoView.__Set):
            raise TypeError(f"'<' not supported between instances of '{type(self).__name__}' and '{type(other).__name__}'")
        if not isinstance(other, IsoView | FrozenIsoView):
            return self.__set < other
        if len(self.__set) >= len(other.set):
            return False
        comp = FrozenIsoView.compare(self, other)
        return comp.source_complete and not comp.destination_complete
    
    def __ge__(self, other: Set[Any]) -> bool:
        if self is other:
            return True
        if not isinstance(other, FrozenIsoView.__Set):
            raise TypeError(f"'>=' not supported between instances of '{type(self).__name__}' and '{type(other).__name__}'")
        if not isinstance(other, IsoView | FrozenIsoView):
            return self.__set >= other
        if len(self.__set) < len(other.set):
            return False
        comp = FrozenIsoView.compare(self, other)
        return comp.destination_complete
    
    def __gt__(self, other: Set[Any]) -> bool:
        if self is other:
            return False
        if not isinstance(other, FrozenIsoView.__Set):
            raise TypeError(f"'>' not supported between instances of '{type(self).__name__}' and '{type(other).__name__}'")
        if not isinstance(other, IsoView | FrozenIsoView):
            return self.__set > other
        if len(self.__set) <= len(other.set):
            return False
        comp = FrozenIsoView.compare(self, other)
        return comp.destination_complete and not comp.source_complete
    
    def __and__(self, other : Set[K2]) -> "FrozenIsoView[K1]":
        if not isinstance(other, FrozenIsoView.__Set):
            return NotImplemented
        if isinstance(other, IsoView | FrozenIsoView):
            return self.intersection(other)
        return FrozenIsoView(self.__set & other)
    
    def __rand__(self, other : Set[K2]) -> "FrozenIsoView[K2]":
        if not isinstance(other, FrozenIsoView.__Set):
            return NotImplemented
        return FrozenIsoView(FrozenIsoSet(other & self.__set))
            
    def __or__(self, other : Set[K2]) -> "FrozenIsoView[K1 | K2]":
        if not isinstance(other, FrozenIsoView.__Set):
            return NotImplemented
        if isinstance(other, IsoView | FrozenIsoView):
            return self.union(other)
        return FrozenIsoView(FrozenIsoSet(other & self.__set))
    
    def __ror__(self, other : Set[K2]) -> "FrozenIsoView[K1 | K2]":
        if not isinstance(other, FrozenIsoView.__Set):
            return NotImplemented
        return FrozenIsoView(FrozenIsoSet(other | self.__set))
    
    def __sub__(self, other : Set[K2]) -> "FrozenIsoView[K1]":
        if not isinstance(other, FrozenIsoView.__Set):
            return NotImplemented
        if isinstance(other, IsoView | FrozenIsoView):
            return self.difference(other)
        return FrozenIsoView(self.__set - other)
    
    def __rsub__(self, other : Set[K2]) -> "FrozenIsoView[K2]":
        if not isinstance(other, FrozenIsoView.__Set):
            return NotImplemented
        r = other - self.__set
        if not isinstance(r, IsoSet):
            r = IsoSet(r)
        return FrozenIsoView.__freeze(IsoView(r))
    
    def __xor__(self, other : Set[K2]) -> "FrozenIsoView[K1 | K2]":
        if not isinstance(other, FrozenIsoView.__Set):
            return NotImplemented
        if isinstance(other, IsoView | FrozenIsoView):
            return self.symmetric_difference(other)
        return FrozenIsoView(self.__set ^ other)
    
    def __rxor__(self, other : Set[K2]) -> "FrozenIsoView[K1 | K2]":
        if not isinstance(other, FrozenIsoView.__Set):
            return NotImplemented
        r = other ^ self.__set
        if not isinstance(r, IsoSet):
            r = IsoSet(r)
        return FrozenIsoView.__freeze(IsoView(r))
    
    def __matmul__(self, other : "IsoSet[K2] | IsoView[K2] | FrozenIsoSet[K2] | FrozenIsoView[K2]") -> "IsoMappings[K1, K2]":
        """
        Implements self @ other. Returns the IsoMappings between two IsoViews
        """
        if not isinstance(other, IsoSet | IsoView | FrozenIsoSet | FrozenIsoView):
            return NotImplemented
        if isinstance(other, IsoSet | FrozenIsoSet):
            other = other.iso_view
        return IsoView.compare(self, other)





V1 = TypeVar("V1")
V2 = TypeVar("V2")

class IsoDictKeys(KeysView[K1], Generic[K1, V1]):

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

    def __init__(self, mapping: "IsoDict[K1, V1]", raw_table : dict[int, dict[int, tuple[K1, V1]]]) -> None:
        if not isinstance(mapping, IsoDict):
            raise TypeError(f"Expected IsoDict, got '{type(mapping).__name__}'")
        self.__mapping = mapping
        self.__table = raw_table

    @property
    def mapping(self) -> "IsoDict[K1, V1]":
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
            value_hdict : "dict[int, tuple[K1, V1]]" = value.__table.get(h, {})
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
            other_hdict : "dict[int, tuple[K1, V1]]" = other.__table.get(h, {})
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
            other_hdict : "dict[int, tuple[K1, V1]]" = other.__table.get(h, {})
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
            other_hdict : "dict[int, tuple[K1, V1]]" = other.__table.get(h, {})
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
            other_hdict : "dict[int, tuple[K1, V1]]" = other.__table.get(h, {})
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
    
    def __iter__(self) -> Iterator[K1]:
        return (k for hvalues in self.__table.values() for k, v in hvalues.values())
    
    def __reversed__(self) -> Iterator[K1]:
        return (k for hvalues in reversed(self.__table.values()) for k, v in reversed(hvalues.values()))
    
    def __len__(self) -> int:
        return len(self.__mapping)
    
    def isdisjoint(self, other: Iterable[Any]) -> bool:
        return all(k not in self for k in other)
    
    def __and__(self, other: Iterable[K2]) -> IsoSet[K1]:
        return IsoSet(self) & IsoSet(other)
    
    def __rand__(self, other: Iterable[K2]) -> IsoSet[K2]:
        return IsoSet(other) & IsoSet(self)

    def __or__(self, other: Iterable[K2]) -> IsoSet[K1 | K2]:
        return IsoSet(self) | IsoSet(other)
    
    def __ror__(self, other: Iterable[K2]) -> IsoSet[K1 | K2]:
        return IsoSet(other) | IsoSet(self)
    
    def __sub__(self, other: Iterable[K2]) -> IsoSet[K1]:
        return IsoSet(self) - IsoSet(other)
    
    def __rsub__(self, other: Iterable[K2]) -> IsoSet[K2]:
        return IsoSet(other) - IsoSet(self)
    
    def __xor__(self, other: Iterable[K2]) -> IsoSet[K1 | K2]:
        return IsoSet(self) ^ IsoSet(other)
    
    def __rxor__(self, other: Iterable[K2]) -> IsoSet[K1 | K2]:
        return IsoSet(other) ^ IsoSet(self)





class FrozenIsoDictKeys(IsoDictKeys[K1, V1]):

    def __init__(self, mapping: "FrozenIsoDict[K1, V1]", raw_table: dict[int, dict[int, tuple[K1, V1]]]) -> None:
        super().__init__(mapping, raw_table)

    @property
    def mapping(self) -> "FrozenIsoDict[K1, V1]":
        return super().mapping # type: ignore
    




class IsoDictValues(ValuesView[V1], Generic[K1, V1]):

    """
    This is the equivalent class of dict_values that list values of IsoDicts.
    """

    from collections.abc import ValuesView as __ValuesView

    __slots__ = {
        "__mapping" : "The mapping that this view refers to.",
        "__table" : "The association table used to store all the elements of the IsoDict."
    }

    def __init__(self, mapping: "IsoDict[K1, V1]", raw_table : dict[int, dict[int, tuple[K1, V1]]]) -> None:
        if not isinstance(mapping, IsoDict):
            raise TypeError(f"Expected IsoDict, got '{type(mapping).__name__}'")
        self.__mapping = mapping
        self.__table = raw_table

    @property
    def mapping(self) -> "IsoDict[K1, V1]":
        """
        The mapping this view refers to.
        """
        return self.__mapping

    def __repr__(self) -> str:
        return f"{type(self).__name__}([{', '.join(str(v) for v in self)}])"
    
    def __iter__(self) -> Iterator[V1]:
        return (v for hvalues in self.__table.values() for k, v in hvalues.values())
    
    def __reversed__(self) -> Iterator[V1]:
        return (v for hvalues in reversed(self.__table.values()) for k, v in reversed(hvalues.values()))
    
    def __contains__(self, value : V1) -> bool:
        return value in iter(self)
    
    def __len__(self) -> int:
        return len(self.__mapping)
    
    def __eq__(self, value: object) -> bool:
        return isinstance(value, IsoDictValues.__ValuesView) and len(self) == len(value) and all(a == b for a, b in zip(self, value))





class FrozenIsoDictValues(IsoDictValues[K1, V1]):

    def __init__(self, mapping: "FrozenIsoDict[K1, V1]", raw_table: dict[int, dict[int, tuple[K1, V1]]]) -> None:
        super().__init__(mapping, raw_table)

    @property
    def mapping(self) -> "FrozenIsoDict[K1, V1]":
        return super().mapping # type: ignore





class IsoDictItems(ItemsView[K1, V1]):

    """
    This is the equivalent class of dict_items that list items of IsoDicts.
    """

    from collections.abc import Set as __Set, Hashable as __Hashable

    __slots__ = {
        "__mapping" : "The mapping that this view refers to.",
        "__table" : "The association table used to store all the elements of the IsoDict."
    }

    def __init__(self, mapping: "IsoDict[K1, V1]", raw_table : dict[int, dict[int, tuple[K1, V1]]]) -> None:
        if not isinstance(mapping, IsoDict):
            raise TypeError(f"Expected IsoDict, got '{type(mapping).__name__}'")
        self.__mapping = mapping
        self.__table = raw_table

    @property
    def mapping(self) -> "IsoDict[K1, V1]":
        """
        The mapping this view refers to.
        """
        return self.__mapping
    
    def __repr__(self) -> str:
        return f"{type(self).__name__}([{', '.join(str(t) for t in self)}])"
    
    def __iter__(self) -> Iterator[tuple[K1, V1]]:
        return ((k, v) for hvalues in self.__table.values() for k, v in hvalues.values())
    
    def __reversed__(self) -> Iterator[tuple[K1, V1]]:
        return ((k, v) for hvalues in reversed(self.__table.values()) for k, v in reversed(hvalues.values()))
    
    def __len__(self) -> int:
        return len(self.__mapping)
    
    def __contains__(self, item: object) -> bool:
        if not isinstance(item, tuple) or len(item) != 2:
            return False
        k, v = item
        if not isinstance(k, IsoDictItems.__Hashable):
            return False
        return k in self.__mapping and self.__mapping[k] == v # type: ignore
    
    def __eq__(self, value: object) -> bool:
        if not isinstance(value, IsoDictItems.__Set):
            return False
        return len(self) == len(value) and all(k in value for k in self)
    
    def isdisjoint(self, other: Iterable[Any]) -> bool:
        return all(k not in self for k in other)
    
    def __and__(self, other: Iterable[tuple[K2, V2]]) -> IsoSet[tuple[K1, V1]]:
        return IsoSet(self) & IsoSet(other)
    
    def __rand__(self, other: Iterable[tuple[K2, V2]]) -> IsoSet[tuple[K2, V2]]:
        return IsoSet(other) & IsoSet(self)

    def __or__(self, other: Iterable[tuple[K2, V2]]) -> IsoSet[tuple[K1, V1] | tuple[K2, V2]]:
        return IsoSet(self) | IsoSet(other)
    
    def __ror__(self, other: Iterable[tuple[K2, V2]]) -> IsoSet[tuple[K1, V1] | tuple[K2, V2]]:
        return IsoSet(other) | IsoSet(self)
    
    def __sub__(self, other: Iterable[tuple[K2, V2]]) -> IsoSet[tuple[K1, V1]]:
        return IsoSet(self) - IsoSet(other)
    
    def __rsub__(self, other: Iterable[tuple[K2, V2]]) -> IsoSet[tuple[K2, V2]]:
        return IsoSet(other) - IsoSet(self)
    
    def __xor__(self, other: Iterable[tuple[K2, V2]]) -> IsoSet[tuple[K1, V1] | tuple[K2, V2]]:
        return IsoSet(self) ^ IsoSet(other)
    
    def __rxor__(self, other: Iterable[tuple[K2, V2]]) -> IsoSet[tuple[K1, V1] | tuple[K2, V2]]:
        return IsoSet(other) ^ IsoSet(self)
    




class FrozenIsoDictItems(IsoDictItems[K1, V1]):

    def __init__(self, mapping: "FrozenIsoDict[K1, V1]", raw_table: dict[int, dict[int, tuple[K1, V1]]]) -> None:
        super().__init__(mapping, raw_table)

    @property
    def mapping(self) -> "FrozenIsoDict[K1, V1]":
        return super().mapping # type: ignore





class IsoDict(MutableMapping[K1, V1]):

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
    def __init__(self: "IsoDict[str, V1]", **kwargs: V1) -> None:
        ...

    @overload
    def __init__(self, iterable: Mapping[K1, V1]) -> None:
        ...

    @overload
    def __init__(self: "IsoDict[str, V1]", iterable: Mapping[str, V1], **kwargs: V1) -> None:
        ...

    @overload
    def __init__(self, iterable: Iterable[tuple[K1, V1]]) -> None:
        ...

    @overload
    def __init__(self: "IsoDict[str, V1]", iterable: Iterable[tuple[str, V1]], **kwargs: V1) -> None:
        ...

    def __init__(self, iterable = (), **kwargs) -> None:
        if not isinstance(iterable, IsoDict.__Iterable):
            raise TypeError(f"Expected iterable, got '{type(iterable)}'")
        if isinstance(iterable, IsoDict.__Mapping):
            iterable = iterable.items()
        
        self.__table : "dict[int, dict[int, tuple[K1, V1]]]" = {}
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
    def fromkeys(cls, iterable : Iterable[K1], value : V1) -> "IsoDict[K1, V1]":
        ...

    @overload
    @classmethod
    def fromkeys(cls, iterable : Iterable[K1], value : None = None) -> "IsoDict[K1, None]":
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
    
    def __iter__(self) -> Iterator[K1]:
        """
        Implements iter(self).
        """
        return (k for hvalues in self.__table.values() for k, v in hvalues.values())
    
    def __reversed__(self) -> Iterator[K1]:
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
    
    def __getitem__(self, k: K1) -> V1:
        if not isinstance(k, IsoDict.__Hashable):
            raise TypeError(f"unhashable type: '{type(k).__name__}'")
        h = hash(k)
        if h in self.__table and id(k) in self.__table[h]:
            return self.__table[h][id(k)][1]
        raise KeyError(k)
    
    def __setitem__(self, k: K1, v: V1) -> None:
        if not isinstance(k, IsoDict.__Hashable):
            raise TypeError(f"unhashable type: '{type(k).__name__}'")
        h = hash(k)
        hmap = self.__table.setdefault(h, {})
        i = id(k)
        if i not in hmap:
            self.__len += 1
        hmap[i] = (k, v)

    def __delitem__(self, k: K1) -> None:
        if not isinstance(k, IsoDict.__Hashable):
            raise TypeError(f"unhashable type: '{type(k).__name__}'")
        h = hash(k)
        if h in self.__table and (i := id(k)) in (hmap := self.__table[h]):
            hmap.pop(i)
            self.__len -= 1
            if not hmap:
                self.__table.pop(h)
        raise KeyError(k)
    
    def clear(self) -> None:
        self.__table.clear()
        self.__len = 0

    def copy(self) -> "IsoDict[K1, V1]":
        """
        Return a shallow copy of an IsoDict.
        """
        cp = IsoDict()
        cp.__table = {h : hdict.copy() for h, hdict in self.__table.items()}
        cp.__len = self.__len
        return cp
    
    def pop(self, k : K1) -> V1:
        if not isinstance(k, IsoDict.__Hashable):
            raise TypeError(f"unhashable type: '{type(k).__name__}'")
        h = hash(k)
        if h in self.__table and (i := id(k)) in (hmap := self.__table[h]):
            v = hmap.pop(i)[1]
            self.__len -= 1
            if not hmap:
                self.__table.pop(h)
            return v
        raise KeyError(k)
    
    def popitem(self) -> tuple[K1, V1]:
        """
        Remove and return an arbitrary IsoDict element.
        Raises KeyError if the IsoDict is empty.
        """
        if not self:
            raise KeyError("'popitem(): IsoDict is empty'")
        h, hmap = self.__table.popitem()
        i, e = hmap.popitem()
        if hmap:
            self.__table[h] = hmap
        self.__len -= 1
        return e
    
    def setdefault(self, k : K1, default : V1) -> V1:
        if not isinstance(k, IsoDict.__Hashable):
            raise TypeError(f"unhashable type: '{type(k).__name__}'")
        if k in self:
            return self[k]
        h = hash(k)
        self.__len += 1
        return self.__table.setdefault(h, {}).setdefault(id(k), (k, default))[1]
    
    def get(self, k : K1, default : V1 | V2 = None) -> V1 | V2:
        if not isinstance(k, IsoDict.__Hashable):
            raise TypeError(f"unhashable type: '{type(k).__name__}'")
        h = hash(k)
        if h in self.__table and id(k) in self.__table[h]:
            return self.__table[h][id(k)][1]
        return default
    
    @overload
    def update(self, iterable : Mapping[K1, V1] | Iterable[tuple[K1, V1]]):
        ...

    @overload
    def update(self : "IsoDict[str, V1]", iterable : Mapping[str, V1] | Iterable[tuple[str, V1]], **kwargs : V1):
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
    
    def items(self) -> IsoDictItems[K1, V1]:
        return IsoDictItems(self, self.__table)

    def keys(self) -> IsoDictKeys[K1, V1]:
        return IsoDictKeys(self, self.__table)

    def values(self) -> IsoDictValues[K1, V1]:
        return IsoDictValues(self, self.__table)

    def __eq__(self, value: object) -> bool:
        if self is value:
            return True
        if not isinstance(value, IsoDict.__Mapping):
            return False
        return len(self) == len(value) and all(k in value for k in self) and all(self[k] == value[k] for k in self)
    
    def __sizeof__(self) -> int:
        return super().__sizeof__() + IsoDict.__getsizeof(self.__table) + sum(IsoDict.__getsizeof(hdict) for hdict in self.__table.values())
    
    def __or__(self, other : Mapping[K1, V1]) -> "IsoDict[K1, V1]":
        if not isinstance(other, IsoDict.__Mapping):
            return NotImplemented
        s = self.copy()
        for k, v in other.items():
            s[k] = v
        return s
    
    def __ror__(self, other : Mapping[K1, V1]) -> "IsoDict[K1, V1]":
        if not isinstance(other, IsoDict.__Mapping):
            return NotImplemented
        s = IsoDict(other)
        for k, v in self.items():
            s[k] = v
        return s
    
    def __ior__(self, other : Mapping[K1, V1]) -> "IsoDict[K1, V1]":
        if not isinstance(other, IsoDict.__Mapping):
            return NotImplemented
        for k, v in other.items():
            self[k] = v
        return self
    




class FrozenIsoDict(IsoDict[K1, V1]):

    """
    Frozen (immutable) version of IsoDicts.
    """

    __slots__ = {
        "__hash" : "The hash of the FrozenIsoDict"
    }

    def __reduce__(self):
        return FrozenIsoDict, (IsoDict(self), )

    def __delitem__(self, v : V1):
        raise TypeError(f"'{type(self).__name__}' object doesn't support item deletion")

    def __ior__(self, __value : Mapping[K1, V1]):
        return NotImplemented

    def __setitem__(self, k : K1, v : V1):
        raise TypeError(f"'{type(self).__name__}' object does not support item assignment")

    def clear(self):
        raise AttributeError(f"'{type(self).__name__}' object has no attribute 'clear'")

    def copy(self):
        return FrozenIsoDict(self)
    
    def pop(self, k : K1) -> V1:
        raise AttributeError(f"'{type(self).__name__}' object has no attribute 'pop'")
    
    def popitem(self) -> tuple[K1, V1]:
        raise AttributeError(f"'{type(self).__name__}' object has no attribute 'popitem'")
    
    def setdefault(self, __key : K1, __default : V1):
        raise AttributeError(f"'{type(self).__name__}' object has no attribute 'setdefault'")
    
    def update(self, iterable : Mapping[K1, V1]):
        raise AttributeError(f"'{type(self).__name__}' object has no attribute 'update'")
    
    def items(self) -> FrozenIsoDictItems[K1, V1]:
        return FrozenIsoDictItems(self, self._IsoDict__table)       # type: ignore

    def keys(self) -> FrozenIsoDictKeys[K1, V1]:
        return FrozenIsoDictKeys(self, self._IsoDict__table)        # type: ignore

    def values(self) -> FrozenIsoDictValues[K1, V1]:
        return FrozenIsoDictValues(self, self._IsoDict__table)      # type: ignore
    
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
    
    def __or__(self, __value: Mapping[K1, V1]) -> "FrozenIsoDict[K1, V1]":
        return FrozenIsoDict(super().__or__(__value))
    
    def __ror__(self, __value: Mapping[K1, V1]) -> "FrozenIsoDict[K1, V1]":
        return FrozenIsoDict(super().__ror__(__value))
    
    @staticmethod
    def fromkeys(iterable : Iterable[K1], value : V1 | None = None) -> "FrozenIsoDict[K1, V1 | None]":
        return FrozenIsoDict((k, value) for k in iterable)





K3 = TypeVar("K3", bound=Hashable)
K4 = TypeVar("K4", bound=Hashable)

class IsoMappings(Generic[K1, K2]):

    """
    This class represents all the possible (sub)isomorphic mappings between two IsoViews.
    It might not be bijective nor even a function : some elements on either side might not be mapped.

    Note that to work properly, all the __eq__ methods called are considered to be equivalence relations (symmetrical, reflexive and transitive), that __hash__ always return the same result and if two objects have different hashes, they will not be equal.
    
    Example: Given a test class:
    >>> class test:
    ...     __existing : dict[str, int] = {}
    ...     def __init__(self, name : str):
    ...         self.name = name
    ...         self.rank = test.__existing.setdefault(name, 1)
    ...         test.__existing[name] += 1
    ...     def __eq__(self, other):
    ...         return isinstance(other, test) and self.name == other.name
    ...     def __hash__(self):
    ...         return hash(self.name)
    ...     def __repr__(self) -> str:
    ...         return f"test({self.name})[{self.rank}]"
    ... 
    
    One can define two IsoSets of elements of this class and list all the ways they can be matched to each other:
    >>> s1 = IsoSet((
    ...     test("A"),
    ...     test("A"),
    ...     test("A"),
    ...     test("B"),
    ...     test("C"),
    ... ))
    >>> s1 = IsoSet((
    ...     test("A"),
    ...     test("A"),
    ...     test("B"),
    ...     test("B"),
    ...     test("D"),
    ... ))
    >>> comp = IsoView.compare(s1.iso_view, s2.iso_view)
    >>> print(s1)
    {A1, A2, A3, B1, C1}
    >>> print(s2)
    {A4, A5, B2, B3, D1}
    >>> m = list(comp)[0]
    >>> for k, v in m.items():
    ...     print(f"{k} -> {v}")
    ... 
    """

    from math import comb, factorial
    from collections.abc import Set as __Set, Iterable as __Iterable, Hashable as __Hashable
    from weakref import WeakSet as __WeakSet
    __comb = staticmethod(comb)
    __factorial = staticmethod(factorial)
    del comb, factorial



    class IsoMapping(FrozenIsoDict[K3, K4]):

        """
        An instance of one possible mapping between two IsoSets.
        """

        from collections.abc import Hashable as __Hashable



        class __VirtualDict(dict):

            """
            Internal class used to simulate the behavior of a dictionnary over the current mapping.
            """

            def __init__(self, source_table : dict[int, dict[int, K3]], destination_table : dict[int, dict[int, K4]], mapping : dict[int, dict[int, int]]):
                self.__source_table = source_table
                self.__destination_table = destination_table
                self.__mapping = mapping

            def __contains__(self, h : int) -> bool:
                return h in self.__mapping

            def __getitem__(self, h : int) -> dict[int, tuple[K3, K4]]:
                src, dst = self.__source_table[h], self.__destination_table[h]
                return {i : (src[i], dst[j]) for i, j in self.__mapping[h].items()}
            
            def __iter__(self) -> Iterator[int]:
                return iter(self.__mapping)
        
            def __len__(self) -> int:
                return len(self.__mapping)
            
            def get(self, h : int, default : dict[int, tuple[K3, K4]]) -> dict[int, tuple[K3, K4]]:
                if h in self.__mapping:
                    src, dst = self.__source_table[h], self.__destination_table[h]
                    return {i : (src[i], dst[j]) for i, j in self.__mapping[h].items()}
                return default
            
            def items(self):
                return ((h, self[h]) for h in self)
            
            def keys(self):
                return iter(self)

            def values(self):
                return (self[h] for h in self)



        def __init__(self, creator : "IsoMappings[K3, K4]", source_table : dict[int, dict[int, K3]], destination_table : dict[int, dict[int, K4]], source : IsoView[K3] | FrozenIsoView[K3], destination : IsoView[K4] | FrozenIsoView[K4], mapping : dict[int, dict[int, int]], size : int) -> None:
            self.__creator = creator
            self.__source_table = source_table
            self.__destination_table = destination_table
            self.__source = source
            self.__destination = destination
            self.__mapping = mapping
            self.__len = size

        @property
        def mappings(self) -> "IsoMappings[K3, K4]":
            """
            Returns the IsoMappings that this mapping instance originated from.
            """
            return self.__creator

        @property
        def source_complete(self) -> bool:
            """
            This indicates if all elements of the source set could be mapped to at least one element in the destination.
            (This means the generated isomorphisms will be functions from the source set.)
            """
            return self.__len == len(self.__source)
        
        @property
        def destination_complete(self) -> bool:
            """
            This indicates if all elements of the destination set could be mapped to at least one element in the source.
            (This means that the generated isomorphisms will be surjective.)
            """
            return self.__len == len(self.__destination)
        
        @property
        def source(self) -> IsoView[K3] | FrozenIsoView[K3]:
            """
            The source IsoView or FrozenIsoView of this IsoMapping.
            """
            return self.__source
        
        @property
        def destination(self) -> IsoView[K4] | FrozenIsoView[K4]:
            """
            The destination IsoView or FrozenIsoView of this IsoMapping.
            """
            return self.__destination

        @staticmethod
        def fromkeys(iterable: Iterable, value: Any | None = None):
            raise AttributeError("'IsomorphMapping' object has no attribute 'fromkeys'")
        
        def __str__(self) -> str:
            return "{" + ", ".join(f"{k1} -> {k2}" for k1, k2 in self.items()) + "}"

        def __contains__(self, key : object) -> bool:
            """
            Implements key in self. Returns True if the element from the source is mapped to an element in the destination in this mapping.
            """
            if not isinstance(key, IsoMappings.IsoMapping.__Hashable):
                raise TypeError(f"unhashable type: '{type(key).__name__}'")
            h = hash(key)
            return h in self.__mapping and id(key) in self.__mapping[h]

        def __iter__(self) -> Iterator[K3]:
            """
            Implements iter(self). Yields all the keys from the source of the mapping.
            """
            return (self.__source_table[h][i] for h, hmap in self.__mapping.items() for i in hmap)
        
        def __reversed__(self) -> Iterator[K3]:
            """
            Implements reversed(self). Yields all the keys from the source of the mapping.
            """
            return (self.__source_table[h][i] for h, hmap in reversed(self.__mapping.items()) for i in reversed(hmap))
        
        def __len__(self) -> int:
            """
            Implements len(self). Returns the number of elements mapped between the source and the destination.
            """
            return self.__len
        
        def __getitem__(self, key : K3) -> K4:
            """
            Implements self[key]. Returns the value mapped for this element.
            """
            if not isinstance(key, IsoMappings.IsoMapping.__Hashable):
                raise TypeError(f"unhashable type: '{type(key).__name__}'")
            h = hash(key)
            if h in self.__mapping and id(key) in self.__mapping[h]:
                return self.__destination_table[h][self.__mapping[h][id(key)]]
            raise KeyError(f"'{key}' not in mapping")
        
        def copy(self) -> "IsoMappings.IsoMapping[K3, K4]":
            return IsoMappings.IsoMapping(self.__creator, self.__source_table, self.__destination_table, self.__source, self.__destination, self.__mapping, self.__len)

        def get(self, key : K3, default : K3 | V1 = None) -> K3 | V1:
            """
            Return the value for key if key is in the mapping, else default.
            """
            if not isinstance(key, IsoMappings.IsoMapping.__Hashable):
                raise TypeError(f"unhashable type: '{type(key).__name__}'")
            h = hash(key)
            if h in self.__mapping and id(key) in self.__mapping[h]:
                return self.__destination_table[h][self.__mapping[h][id(key)]]
            return default
        
        def items(self) -> IsoDictItems[K3, K4]:
            return IsoDictItems(self, IsoMappings.IsoMapping.__VirtualDict(self.__source_table, self.__destination_table, self.__mapping))
        
        def keys(self) -> IsoDictKeys[K3, K4]:
            return IsoDictKeys(self, IsoMappings.IsoMapping.__VirtualDict(self.__source_table, self.__destination_table, self.__mapping))
        
        def values(self) -> IsoDictValues[K3, K4]:
            return IsoDictValues(self, IsoMappings.IsoMapping.__VirtualDict(self.__source_table, self.__destination_table, self.__mapping))

        def __sizeof__(self) -> int:
            return object.__sizeof__(self)
        
        def __or__(self, value: Mapping[K3, K4]) -> FrozenIsoDict[K3, K4]:
            return FrozenIsoDict(self) | value
        
        def __ror__(self, value: Mapping[K3, K4]) -> FrozenIsoDict[K3, K4]:
            return value | FrozenIsoDict(self)


    
    class __product:

        """
        An internal specialized implementation of the itertools' product that takes advantage of sequences.
        """
        


        class __permutations:

            """
            An internal specialized implementation of the itertools' permutations that does satisfy the Sequence type.
            """

            from math import factorial
            __factorial = staticmethod(factorial)
            del factorial

            def __init__(self, seq : Iterable[int], size : int) -> None:
                self.__seq = tuple(seq)
                self.__size = size
                self.__len = type(self).__factorial(len(self.__seq)) // type(self).__factorial(len(self.__seq) - self.__size)

            @property
            def len(self) -> int:
                return self.__len
            
            def __getitem__(self, i : int) -> tuple[int, ...]:
                seq_copy = list(self.__seq)
                m = self.__len
                indices = []
                index_map = {e : i for i, e in enumerate(self.__seq)}
                q, r = i, 0
                for j, _ in zip(reversed(range(len(self.__seq))), range(self.__size)):
                    m //= j + 1
                    q, r = divmod(q, m)
                    i = index_map[seq_copy.pop(q)]
                    indices.append(i)
                    q = r
                return tuple(self.__seq[i] for i in indices)
            


        class __combinations:

            """
            An internal specialized implementation of the itertools' combinations that does satisfy the Sequence type.
            """

            from math import comb
            __comb = staticmethod(comb)
            del comb

            def __init__(self, seq : Iterable[int], size : int) -> None:
                self.__seq = tuple(seq)
                self.__size = size
                self.__len = type(self).__comb(len(self.__seq), size)

            @property
            def len(self) -> int:
                return self.__len
            
            def __getitem__(self, i : int) -> tuple[int, ...]:
                k, n = self.__size, len(self.__seq)
                c = self.__len * k // n
                k -= 1
                n -= 1
                indices = []
                j = 0
                while c:
                    if i < c:
                        indices.append(j)
                        c = c * k // n if n != 0 else 0
                        n -= 1
                        k -= 1
                    else:
                        i -= c
                        c = c * (n - k) // n if n != 0 else 0
                        n -= 1
                    j += 1
                return tuple(self.__seq[i] for i in indices)
            

        
        def __init__(self, mappings : "dict[int, list[tuple[frozenset[int], frozenset[int]]]]") -> None:
            self.__mappings = mappings

        def __iter__(self) -> Iterator[dict[int, dict[int, int]]]:
            """
            Implements iter(self). Yields all the possible mappings.
            """
            choices : "list[tuple[int, IsoMappings.__product.__combinations, IsoMappings.__product.__permutations]]" = []
            sizes : "list[tuple[int, int, int]]" = []
            for h, hmap in self.__mappings.items():
                for src, dst in hmap:
                    a = min(len(src), len(dst))
                    c = type(self).__combinations(src, a)
                    p = type(self).__permutations(dst, a)
                    choices.append((h, c, p))
                    sizes.append((c.len, p.len, c.len * p.len))

            positions : "list[int]" = [0 for _ in sizes]
            total_size = 1
            for _, _, s in sizes:
                total_size *= s

            def increment():
                for i in reversed(range(len(positions))):
                    k = positions[i]
                    positions[i] = (k + 1) % sizes[i][2]
                    if k + 1 < sizes[i][2]:
                        break
                
            def expand_position(i : int) -> tuple[int, int]:
                _, b, _ = sizes[i]
                return divmod(positions[i], b)

            for _ in range(total_size):
                d : "dict[int, dict[int, int]]" = {}
                indices = (expand_position(i) for i in range(len(positions)))
                for (h, c, p), (i, j) in zip(choices, indices):
                    d.setdefault(h, {}).update({a : b for a, b in zip(c[i], p[j])})
                yield d
                increment()

        def __reversed__(self) -> Iterator[dict[int, dict[int, int]]]:
            """
            Implements reversed(self). Yields all the possible mappings in reversed order.
            """
            choices : "list[tuple[int, IsoMappings.__product.__combinations, IsoMappings.__product.__permutations]]" = []
            sizes : "list[tuple[int, int, int]]" = []
            for h, hmap in self.__mappings.items():
                for src, dst in hmap:
                    a = min(len(src), len(dst))
                    c = type(self).__combinations(src, a)
                    p = type(self).__permutations(dst, a)
                    choices.append((h, c, p))
                    sizes.append((c.len, p.len, c.len * p.len))

            positions : "list[int]" = [s - 1 for _, _, s in sizes]
            total_size = 1
            for _, _, s in sizes:
                total_size *= s

            def decrement():
                for i in reversed(range(len(positions))):
                    k = positions[i]
                    positions[i] = (k - 1) % sizes[i][2]
                    if k - 1 >= 0:
                        break
                
            def expand_position(i : int) -> tuple[int, int]:
                _, b, _ = sizes[i]
                return divmod(positions[i], b)

            for _ in range(total_size):
                d : "dict[int, dict[int, int]]" = {}
                indices = (expand_position(i) for i in range(len(positions)))
                for (h, c, p), (i, j) in zip(choices, indices):
                    d.setdefault(h, {}).update({a : b for a, b in zip(c[i], p[j])})
                yield d
                decrement()

        def __getitem__(self, i : int) -> dict[int, dict[int, int]]:
            """
            Implements self[i]. Returns the i-th mapping in lexicographic order of the cartesian product of the source set and destination set.
            """
            choices : "list[tuple[int, IsoMappings.__product.__combinations, IsoMappings.__product.__permutations]]" = []
            sizes : "list[tuple[int, int, int]]" = []
            for h, hmap in self.__mappings.items():
                for src, dst in hmap:
                    a = min(len(src), len(dst))
                    c = type(self).__combinations(src, a)
                    p = type(self).__permutations(dst, a)
                    choices.append((h, c, p))
                    sizes.append((c.len, p.len, c.len * p.len))

            positions : "list[int]" = [0 for _, _, s in sizes]
            q = i
            p = len(positions)
            while q:
                p -= 1
                q, r = divmod(q, sizes[p][2])
                positions[p] = r
            total_size = 1
            for _, _, s in sizes:
                total_size *= s
                
            def expand_position(i : int) -> tuple[int, int]:
                _, b, _ = sizes[i]
                return divmod(positions[i], b)

            d : "dict[int, dict[int, int]]" = {}
            indices = (expand_position(i) for i in range(len(positions)))
            for (h, c, p), (i, j) in zip(choices, indices):
                d.setdefault(h, {}).update({a : b for a, b in zip(c[i], p[j])})
            return d



    def __init__(self, source_table : dict[int, dict[int, K1]], destination_table : dict[int, dict[int, K2]], source : IsoView[K1] | FrozenIsoView[K1], destination : IsoView[K2] | FrozenIsoView[K2]) -> None:
        self.__source_table = source_table
        self.__destination_table = destination_table
        self.__source = source
        self.__destination = destination
        self.__inverse : "IsoMappings[K2, K1] | None" = None
        self.__mappings : "dict[int, list[tuple[frozenset[int], frozenset[int]]]]" = {}
        self.__len = 1
        self.__map_size = 0
        for h, source_hdict in self.__source_table.items():
            destination_hdict : "dict[int, K2]" = self.__destination_table.get(h, {})

            source_hgroups : "list[tuple[int, ...]]" = []
            for ia, a in source_hdict.items():
                for g in reversed(source_hgroups):
                    if any(a == source_hdict[ib] for ib in g):
                        source_hgroups.append(g + (ia, ))
                        source_hgroups.remove(g)
                        break
                else:
                    source_hgroups.append((ia, ))
    
            destination_hgroups : "list[tuple[int, ...]]" = []
            for ia, a in destination_hdict.items():
                for g in reversed(destination_hgroups):
                    if any(a == destination_hdict[ib] for ib in g):
                        destination_hgroups.append(g + (ia, ))
                        destination_hgroups.remove(g)
                        break
                else:
                    destination_hgroups.append((ia, ))

            hmap : "list[tuple[frozenset[int], frozenset[int]]]" = []
            for s in source_hgroups:
                repr_s = source_hdict[s[0]]
                for d in destination_hgroups:
                    repr_d = destination_hdict[d[0]]
                    if repr_s == repr_d:
                        hmap.append((frozenset(s), frozenset(d)))
                        a, b = min(len(d), len(s)), max(len(d), len(s))
                        self.__len *= IsoMappings.__comb(b, a) * IsoMappings.__factorial(a)
                        self.__map_size += a
                        destination_hgroups.remove(d)
                        break
            self.__mappings[h] = hmap
        if not self.__map_size:
            self.__len = 0

    @classmethod
    def __from_inverse(cls, inverse : "IsoMappings[K1, K2]") -> "IsoMappings[K2, K1]":
        """
        Internal function used to generate the inverse mappings from the original mappings.
        """
        self : "IsoMappings[K2, K1]" = cls.__new__(cls)
        self.__source_table = inverse.__destination_table
        self.__destination_table = inverse.__source_table
        self.__source = inverse.__destination
        self.__destination = inverse.__source
        self.__inverse = None
        self.__mappings = {h : [(d, s) for s, d in hmap] for h, hmap in inverse.__mappings.items()}
        self.__len = inverse.__len
        return self
    
    @property
    def inverse(self) -> "IsoMappings[K2, K1]":
        """
        Returns the inverse mappings of this mappings.
        """
        if self.__inverse is None:
            self.__inverse = self.__from_inverse(self)
        return self.__inverse

    @property
    def source_complete(self) -> bool:
        """
        This indicates if all elements of the source set could be mapped to at least one element in the destination.
        (This means the generated isomorphisms will be functions from the source set.)
        """
        return self.__map_size == len(self.__source)
    
    @property
    def destination_complete(self) -> bool:
        """
        This indicates if all elements of the destination set could be mapped to at least one element in the source.
        (This means that the generated isomorphisms will be surjective.)
        """
        return self.__map_size == len(self.__destination)
    
    @property
    def source(self) -> IsoView[K1] | FrozenIsoView[K1]:
        """
        The source IsoView or FrozenIsoView of this IsoMapping.
        """
        return self.__source
    
    @property
    def destination(self) -> IsoView[K2] | FrozenIsoView[K2]:
        """
        The destination IsoView or FrozenIsoView of this IsoMapping.
        """
        return self.__destination
    
    @property
    def map_size(self) -> int:
        """
        The number of elements in the source/destination that can be associated by the mappings.
        Same result as len(m) for m any mapping in self.
        """
        return self.__map_size
    
    def __repr__(self) -> str:
        return f"{type(self).__name__}({repr(self.source)}, {repr(self.destination)})"
    
    def __str__(self) -> str:
        return f"{self.source} -> {self.destination}"
    
    def __len__(self) -> int:
        """
        Implements len(self). Returns the number of possible maximal non-empty mappings between the source and destination.
        """
        return self.__len
    
    def __bool__(self) -> bool:
        """
        Implements bool(self). Returns True if at least one non-empty mapping exists between the source and the destination.
        """
        return self.__len != 0
    
    def __hash__(self) -> int:
        """
        Implements hash(self).
        """
        return hash(sum(hash(mi) for mi in self))
    
    def __eq__(self, value: object) -> bool:
        return isinstance(value, IsoMappings) and self.source == value.source and self.destination == value.destination

    def __getitem__(self, i : int) -> IsoMapping[K1, K2]:
        """
        Implements self[k].
        Returns the i-th mapping in lexicographic order of the cartesian product of the source set and destination set.
        (Supposing the sets have an order and the product is ordered as would itertools.product.)
        """
        if not isinstance(i, int):
            raise TypeError(f"Expected int, got '{type(i).__name__}'")
        if i < 0:
            i += len(self)
        if i < 0 or i >= len(self):
            raise IndexError(f"IsoMappings index out of range : {i}")
        return IsoMappings.IsoMapping(self, self.__source_table, self.__destination_table, self.__source, self.__destination, type(self).__product(self.__mappings)[i], self.__map_size)
        
    def __contains__(self, k : object) -> bool:
        """
        Implements k in self.
        Returns True if any of the mappings can map the given key to another in the destination.
        """
        return any(k in mi for mi in self)
    
    def __iter__(self) -> Iterator[IsoMapping[K1, K2]]:
        """
        Implements iter(self). Yields all the possible mappings between the source IsoSet and the destination IsoSet.
        """
        for d in type(self).__product(self.__mappings):
            yield IsoMappings.IsoMapping(self, self.__source_table, self.__destination_table, self.__source, self.__destination, d, self.__map_size)

    def __reversed__(self) -> Iterator[IsoMapping[K1, K2]]:
        """
        Implements reversed(self). Yields all the possible mappings between the source IsoSet and the destination IsoSet.
        """
        for d in reversed(type(self).__product(self.__mappings)):
            yield IsoMappings.IsoMapping(self, self.__source_table, self.__destination_table, self.__source, self.__destination, d, self.__map_size)        
    
    def __invert__(self) -> "IsoMappings[K2, K1]":
        """
        Implements ~self. Returns the inverse mappings.
        """
        return self.inverse
        




del K1, K2, V1, V2, K3, K4, ItemsView, Iterator, MutableSet, KeysView, Mapping, MutableMapping, ValuesView, Set, Hashable, Iterable, Any, Generic, TypeVar, overload