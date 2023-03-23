from __future__ import annotations

import itertools
import re
from functools import cached_property
import math
import copy

from .color import Color
from .segmenttree import SegmentTree

PROPERTY_TYPES = [property, cached_property]


class DataNotFound(Exception):
    pass


def _is_property(a):
    return any(isinstance(a, pt) for pt in PROPERTY_TYPES)


def _for_all_in_tree(tree, f):
    for k, v in list(tree.items()):
        match v:
            case dict():
                _for_all_in_tree(v, f)

            case list():
                tree[k] = [f(d) for d in v]

            case _:
                tree[k] = f(v)


class _DataBinder:
    def bind(self, data):
        return data


class _ContainerBinder(_DataBinder):
    def __init__(self, container):
        self.container = container

    def bind(self, data):
        return self.container(data)


class _ListBinder(_ContainerBinder):
    def bind(self, data_list):
        bind = super().bind
        return [bind(data) for data in data_list]


class DataContainer:
    def __init__(self, data):
        self._data = data

        self._packtree = {}
        self._has_scanned = False

    def _get(self, *path, binder=None):
        if not path:
            raise ValueError()

        if binder is None:
            binder = _DataBinder()

        try:
            data = self._data
            for key in path:
                data = data[key]
            data = binder.bind(data)

        except KeyError:
            path_string = "".join(f"[{k}]" for k in path)
            raise DataNotFound(f"Could not find {type(self).__name__}.data{path_string}")

        tree = self._packtree
        for key in path[:-1]:
            tree = tree.setdefault(key, {})
        tree.setdefault(path[-1], data)

        return data

    def _get_to_container(self, container, *path):
        return self._get(*path, binder=_ContainerBinder(container))

    def _get_to_container_list(self, container, *path):
        return self._get(*path, binder=_ListBinder(container))

    def pack(self):
        if not self._has_scanned:
            self_class = self.__class__
            for an in dir(self_class):
                if _is_property(getattr(self_class, an)):
                    getattr(self, an)

            _for_all_in_tree(self._packtree, lambda d: d if not isinstance(d, DataContainer) else d.pack())

            self._has_scanned = True

        return copy.deepcopy(self._packtree)


class World(DataContainer):
    def __str__(self):
        return f"(Time: {self.time}, Population: {self.population})"

    @cached_property
    def organisms(self) -> list[Organism]:
        return self._get_to_container_list(Organism, "organisms", "list")

    @cached_property
    def population(self) -> int:
        return len([o for o in self.organisms if o.alive])

    @property
    def time(self) -> int:
        return self._get("worldStatistics", "time")


class Organism(DataContainer):
    def __str__(self):
        return str(f"ID:{self.id}")

    def __repr__(self):
        return f"<Organism: {self.id}>"

    def __eq__(self, other: Organism):
        if not isinstance(other, Organism):
            return NotImplemented

        return all((
            self.clade == other.clade,
            self.genes == other.genes,
            self.mirror == other.mirror,
            self.symmetry == other.symmetry
        ))

    @property
    def alive(self) -> bool:
        return self._get("alive")

    @property
    def id(self) -> int:
        return self._get("ID")

    @cached_property
    def clade(self) -> Clade:
        return Clade(self._get("geneticCode", "cladeID"))

    @property
    def symmetry(self) -> int:
        return self._get("geneticCode", "symmetry")

    @property
    def mirror(self) -> bool:
        return bool(self._get("geneticCode", "mirror"))

    @cached_property
    def genes(self) -> list[Gene]:
        genes = self._get_to_container_list(Gene, "geneticCode", "genes")

        if not (self.mirror and self.symmetry > 1) and not any(g.branch == 0 for g in genes[1:]):
            genes[0]._data["theta"] = 0.0

        return genes

    @cached_property
    def segment_tree(self) -> SegmentTree:
        return SegmentTree(self)

    @property
    def radius(self) -> float:
        return self.segment_tree.radius


class Gene(DataContainer):
    def __str__(self):
        return f"({self.color.html}, {self.length:.1f}, " \
               f"{round(math.degrees(self.rotation))}\u00b0, Branch {self.branch})"

    def __repr__(self):
        return f"<Gene: {self.color.rgb}>"

    def __eq__(self, other: Gene):
        if not isinstance(other, Gene):
            return NotImplemented

        return all((
            self.rotation == other.rotation,
            self.length == other.length,
            self.branch == other.branch,
            self.color == other.color
        ))

    @property
    def rotation(self) -> float:
        return self._get("theta")

    @property
    def length(self) -> float:
        return self._get("length")

    @property
    def branch(self) -> int:
        return self._get("branch")

    @cached_property
    def color(self) -> Color:
        return Color(self._get("color", "value"))


class Clade:
    def __init__(self, clade_string: str):
        self._string: str = clade_string

        base_id_string, lineage_string = re.match(r"^(?:.*:)?(\d+)([\s\S]*)$", self._string).groups()
        self._base_id: int = int(base_id_string)
        self._lineage: list[str] = re.findall(r"[\da-f]+", lineage_string)

    def __eq__(self, other: Clade):
        if not isinstance(other, Clade):
            return NotImplemented

        return self.has_common_ancestor(other) and self.lineage == other.lineage

    def __hash__(self):
        return hash(self.string)

    def __str__(self):
        return self.string

    def __repr__(self):
        return f"<Clade: {self}>"

    @property
    def string(self) -> str:
        return self._string

    @property
    def base_id(self) -> int:
        return self._base_id

    @property
    def lineage(self) -> list[str]:
        return self._lineage.copy()

    def has_common_ancestor(self, other: Clade) -> bool:
        return self.base_id == other.base_id

    def descends_from(self, other: Clade) -> bool:
        if not self.has_common_ancestor(other):
            return False

        for own_node, other_node in itertools.zip_longest(self.lineage, other.lineage):
            if other_node is None:
                return True
            if own_node != other_node:
                return False
        return False

    def is_direct_ancestor(self, other: Clade) -> bool:
        return self == other or self.descends_from(other)

    def is_direct_relative(self, other: Clade) -> bool:
        return self.is_direct_ancestor(other) or other.is_direct_ancestor(self)

    def distance_from(self, other: Clade) -> int or None:
        return len(self.lineage) - len(other.lineage) if self.is_direct_relative(other) else None
