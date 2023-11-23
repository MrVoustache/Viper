"""
Tests the isomorphic collections of Viper.
"""

from typing import Iterable, TypeVar
from Viper.collections.isomorph import IsoSet, FrozenIsoSet, IsoView
from random import random, choice
from .. import debug, info, warning, error





N_RUNS = 2 ** 8
SIZE = 2 ** 10

class test:
    __existing : dict[str, int] = {}
    def __init__(self, name : str) -> None:
        self.name = name
        self.rank = test.__existing.setdefault(name, 1)
        test.__existing[name] += 1
    def __eq__(self, value: object) -> bool:
        return isinstance(value, test) and self.name == value.name
    def __hash__(self) -> int:
        return hash(self.name)
    def __str__(self) -> str:
        return f"{self.name}{self.rank}"
    def __repr__(self) -> str:
        return f"test({self.name})[{self.rank}]"

info("Testing basic comparison system...")

for n in range(N_RUNS):
    s1 = IsoSet((test("A"), test("A"), test("A"), test("B"), test("C")))
    s2 = IsoSet((test("A"), test("A"), test("B"), test("B"), test("D")))
    comp = IsoView.compare(s1.iso_view, s2.iso_view)

    for i, m in enumerate(comp):
        j = -1
        for j, (k, v) in enumerate(m.items()):
            pass
        assert m == comp[i]
        if j + 1 != len(m):
            i2 = -1
            error("s1 = {" + ", ".join(f"{k} : {id(k)}" for k in s1) + "}")
            error("s2 = {" + ", ".join(f"{k} : {id(k)}" for k in s2) + "}")
            if i2 == i - 1:
                error("Got an invalid size mapping!")
                breakpoint()
            for i2, m in enumerate(comp):
                if i2 == i - 1:
                    error("Got an invalid size mapping!")
                    breakpoint()

T = TypeVar("T")

def subset_iter(it : Iterable[T], prob : float = 0.5) -> Iterable[T]:
    it = tuple(it)
    it2 = it
    while len(it2) == len(it) and prob < 1.0:
        it2 = tuple(k for k in it if random() <= prob)
    yield from it2





warning("Running collections.isomorph tests...")

for n in range(N_RUNS * 16):

    info(f"Going for round #{n + 1}")
    l = [test(choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")) for i in range(SIZE)]

    info(f"Creating main set of size {len(l)}")
    superset = IsoSet(l)

    assert len(superset) == len(l), f"Main set size mismatch: {len(l)} elements created but set size is {len(superset)}"

    debug("Copying set")
    superset_copy = superset.copy()

    assert len(superset) == len(superset_copy), "Main set and copied set have different sizes"

    subset_1 = IsoSet(test("A") for _ in range(len(superset) // 2))
    while len(subset_1) == len(superset) // 2:
        subset_1 = IsoSet(subset_iter(superset))
    info(f"Created first subset of size {len(subset_1)}")

    assert len(subset_1) < len(superset), "Subset has greater or equal size compared to the main set"

    debug("Testing __contain__")
    assert all(k in superset for k in subset_1), "Some elements of the subset are not in the superset"

    subset_2 = IsoSet(k for k in superset if k not in subset_1)
    info(f"Created second disjoint subset of size {len(subset_2)}")

    info("Testing comparison operations")
    debug("Testing == between supersets")
    assert superset == superset_copy
    debug("Testing != between subset and superset")
    assert subset_1 != superset
    debug("Testing != between subsets")
    assert subset_1 != subset_2
    debug("Testing <= between supersets")
    assert superset <= superset_copy
    debug("Testing >= between supersets")
    assert superset >= superset_copy
    debug("Testing < between supersets")
    assert not superset < superset_copy
    debug("Testing > between supersets")
    assert not superset > superset_copy
    debug("Testing <= between subset and superset")
    assert subset_1 <= superset
    debug("Testing <= between subset and superset copy")
    assert subset_1 <= superset_copy
    debug("Testing < between subset and superset")
    assert subset_1 < superset
    debug("Testing >= between superset and subset")
    assert superset >= subset_2
    debug("Testing > between superset and subset")
    assert superset > subset_2
    debug("Testing <= between subsets")
    assert not subset_1 <= subset_2
    debug("Testing >= between subsets")
    assert not subset_1 >= subset_2

    info("Testing set operations")
    debug("Testing | between subset and superset")
    assert subset_1 | superset == superset_copy
    debug("Testing & between subset and superset")
    assert subset_1 & superset_copy == subset_1
    debug("Testing ^ between subsets")
    assert subset_1 ^ subset_2 == superset
    debug("Testing ^ between subset and superset")
    assert subset_2 ^ superset == subset_1
    debug("Testing - between superset and subset")
    assert superset - subset_1 == subset_2
    debug("Testing - between supersets")
    assert superset - superset_copy == IsoSet()

    debug("Testing isdisjoint between subsets")
    assert subset_1.isdisjoint(subset_2)
    debug("Testing issubset between subset and superset")
    assert subset_1.issubset(superset)
    debug("Testing issuperset between superset and subset")
    assert superset.issuperset(subset_1)
    debug("Testing issubset between superset and subset")
    assert not superset.issubset(subset_1)
    debug("Testing issuperset between subset and superset")
    assert not subset_1.issuperset(superset)


    info("Generating isomorphic distinct copies of the sets")
    superset_iso = IsoSet(test(t.name) for t in superset)

    debug("Converting into IsoViews")
    subset_1 = IsoSet(k for k in superset if k.name in "ABCDEFGHIJKLM").iso_view
    subset_2 = IsoSet(k for k in superset if k.name not in "ABCDEFGHIJKLM").iso_view
    superset = superset.iso_view
    superset_iso = superset_iso.iso_view

    info("Testing comparison operations")
    debug("Testing == between supersets")
    assert superset == superset_iso
    debug("Testing != between subset and superset")
    assert subset_1 != superset
    debug("Testing != between subsets")
    assert subset_1 != subset_2
    debug("Testing <= between supersets")
    assert superset <= superset_iso
    debug("Testing >= between supersets")
    assert superset >= superset_iso
    debug("Testing < between supersets")
    assert not superset < superset_iso
    debug("Testing > between supersets")
    assert not superset > superset_iso
    debug("Testing <= between subset and superset")
    assert subset_1 <= superset
    debug("Testing <= between subset and superset copy")
    assert subset_1 <= superset_iso
    debug("Testing < between subset and superset")
    assert subset_1 < superset
    debug("Testing >= between superset and subset")
    assert superset >= subset_2
    debug("Testing > between superset and subset")
    assert superset > subset_2
    debug("Testing <= between subsets")
    assert not subset_1 <= subset_2
    debug("Testing >= between subsets")
    assert not subset_1 >= subset_2

    info("Testing set operations")
    debug("Testing isdisjoint between subsets")
    assert subset_1.isdisjoint(subset_2)
    debug("Testing issubset between subset and superset")
    assert subset_1.issubset(superset)
    debug("Testing issuperset between superset and subset")
    assert superset.issuperset(subset_1)
    debug("Testing issubset between superset and subset")
    assert not superset.issubset(subset_1)
    debug("Testing issuperset between subset and superset")
    assert not subset_1.issuperset(superset)

    debug("Testing | between subset and superset")
    assert subset_1 | superset == superset_iso
    debug("Testing & between subset and superset")
    assert subset_1 & superset_iso == subset_1
    debug("Testing ^ between subsets")
    assert subset_1 ^ subset_2 == superset
    debug("Testing ^ between subset and superset")
    assert subset_2 ^ superset == subset_1
    debug("Testing - between superset and subset")
    assert superset - subset_1 == subset_2
    debug("Testing - between supersets")
    assert superset - superset_iso == IsoSet()


    info(f"Switching to Frozen versions")
    superset = FrozenIsoSet(l)

    assert len(superset) == len(l), f"Main set size mismatch: {len(l)} elements created but set size is {len(superset)}"

    debug("Copying set")
    superset_copy = superset.copy()

    assert len(superset) == len(superset_copy), "Main set and copied set have different sizes"

    subset_1 = FrozenIsoSet(test("A") for _ in range(len(superset) // 2))
    while len(subset_1) == len(superset) // 2:
        subset_1 = FrozenIsoSet(subset_iter(superset))
    info(f"Created first subset of size {len(subset_1)}")

    assert len(subset_1) < len(superset), "Subset has greater or equal size compared to the main set"

    debug("Testing __contain__")
    assert all(k in superset for k in subset_1), "Some elements of the subset are not in the superset"

    subset_2 = FrozenIsoSet(k for k in superset if k not in subset_1)
    info(f"Created second disjoint subset of size {len(subset_2)}")

    info("Testing comparison operations")
    debug("Testing == between supersets")
    assert superset == superset_copy
    debug("Testing != between subset and superset")
    assert subset_1 != superset
    debug("Testing != between subsets")
    assert subset_1 != subset_2
    debug("Testing <= between supersets")
    assert superset <= superset_copy
    debug("Testing >= between supersets")
    assert superset >= superset_copy
    debug("Testing < between supersets")
    assert not superset < superset_copy
    debug("Testing > between supersets")
    assert not superset > superset_copy
    debug("Testing <= between subset and superset")
    assert subset_1 <= superset
    debug("Testing <= between subset and superset copy")
    assert subset_1 <= superset_copy
    debug("Testing < between subset and superset")
    assert subset_1 < superset
    debug("Testing >= between superset and subset")
    assert superset >= subset_2
    debug("Testing > between superset and subset")
    assert superset > subset_2
    debug("Testing <= between subsets")
    assert not subset_1 <= subset_2
    debug("Testing >= between subsets")
    assert not subset_1 >= subset_2

    info("Testing set operations")
    debug("Testing | between subset and superset")
    assert subset_1 | superset == superset_copy
    debug("Testing & between subset and superset")
    assert subset_1 & superset_copy == subset_1
    debug("Testing ^ between subsets")
    assert subset_1 ^ subset_2 == superset
    debug("Testing ^ between subset and superset")
    assert subset_2 ^ superset == subset_1
    debug("Testing - between superset and subset")
    assert superset - subset_1 == subset_2
    debug("Testing - between supersets")
    assert superset - superset_copy == IsoSet()

    debug("Testing isdisjoint between subsets")
    assert subset_1.isdisjoint(subset_2)
    debug("Testing issubset between subset and superset")
    assert subset_1.issubset(superset)
    debug("Testing issuperset between superset and subset")
    assert superset.issuperset(subset_1)
    debug("Testing issubset between superset and subset")
    assert not superset.issubset(subset_1)
    debug("Testing issuperset between subset and superset")
    assert not subset_1.issuperset(superset)


    info("Generating isomorphic distinct copies of the sets")
    superset_iso = FrozenIsoSet(test(t.name) for t in superset)

    debug("Converting into IsoViews")
    subset_1 = FrozenIsoSet(k for k in superset if k.name in "ABCDEFGHIJKLM").iso_view
    subset_2 = FrozenIsoSet(k for k in superset if k.name not in "ABCDEFGHIJKLM").iso_view
    superset = superset.iso_view
    superset_iso = superset_iso.iso_view

    info("Testing comparison operations")
    debug("Testing == between supersets")
    assert superset == superset_iso
    debug("Testing != between subset and superset")
    assert subset_1 != superset
    debug("Testing != between subsets")
    assert subset_1 != subset_2
    debug("Testing <= between supersets")
    assert superset <= superset_iso
    debug("Testing >= between supersets")
    assert superset >= superset_iso
    debug("Testing < between supersets")
    assert not superset < superset_iso
    debug("Testing > between supersets")
    assert not superset > superset_iso
    debug("Testing <= between subset and superset")
    assert subset_1 <= superset
    debug("Testing <= between subset and superset copy")
    assert subset_1 <= superset_iso
    debug("Testing < between subset and superset")
    assert subset_1 < superset
    debug("Testing >= between superset and subset")
    assert superset >= subset_2
    debug("Testing > between superset and subset")
    assert superset > subset_2
    debug("Testing <= between subsets")
    assert not subset_1 <= subset_2
    debug("Testing >= between subsets")
    assert not subset_1 >= subset_2

    info("Testing set operations")
    debug("Testing isdisjoint between subsets")
    assert subset_1.isdisjoint(subset_2)
    debug("Testing issubset between subset and superset")
    assert subset_1.issubset(superset)
    debug("Testing issuperset between superset and subset")
    assert superset.issuperset(subset_1)
    debug("Testing issubset between superset and subset")
    assert not superset.issubset(subset_1)
    debug("Testing issuperset between subset and superset")
    assert not subset_1.issuperset(superset)

    debug("Testing | between subset and superset")
    assert subset_1 | superset == superset_iso
    debug("Testing & between subset and superset")
    assert subset_1 & superset_iso == subset_1
    debug("Testing ^ between subsets")
    assert subset_1 ^ subset_2 == superset
    debug("Testing ^ between subset and superset")
    assert subset_2 ^ superset == subset_1
    debug("Testing - between superset and subset")
    assert superset - subset_1 == subset_2
    debug("Testing - between supersets")
    assert superset - superset_iso == IsoSet()