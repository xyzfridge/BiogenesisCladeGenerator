from __future__ import annotations

from pyglet.math import Vec2
from math import pi
from functools import cached_property
from typing import Generator

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .datamodel import Organism
    from .color import Color


class Segment:
    def __init__(self, origin: Vec2 or Segment, length: float, rotation: float, color: Color):
        self.rotation: float = rotation
        self.length: float = length
        self.color: Color = color

        if isinstance(origin, Segment):
            self.origin = origin.destination
        elif isinstance(origin, Vec2):
            self.origin = origin
        else:
            raise TypeError()

    @property
    def destination(self) -> Vec2:
        transform = Vec2(self.length, 0.0).rotate(self.rotation)
        destination = self.origin + transform
        return Vec2(*(round(x) for x in destination))

    def xy(self, offset: Vec2 = Vec2(0.0, 0.0)) -> tuple[tuple[float, float], tuple[float, float]]:
        return (
            tuple(self.origin + offset),
            tuple(self.destination + offset)
        )


class SegmentTree:
    def __init__(self, organism: Organism):
        self.subtrees: list[list[Segment]] = [[] for _ in range(organism.symmetry)]
        self.root: Vec2 = Vec2(0.0, 0.0)
        self.mirror: bool = organism.mirror

        for gene in organism.genes:
            self._add_segment(gene.branch, gene.length, gene.rotation, gene.color)

    @property
    def first_subtree(self) -> list[Segment]:
        return self.subtrees[0]

    @property
    def symmetry(self) -> int:
        return len(self.subtrees)

    def _root_and_subtree(self, subtree):
        return [self.root, *subtree]

    def _add_segment(self, branch: int, length: float, rotation: float, color: Color):
        branch = branch if branch < len(self._root_and_subtree(self.first_subtree)) else -1

        for num, subtree in enumerate(self.subtrees):
            origin = [self.root, *subtree][branch]

            mirror_subtree = self.mirror and num % 2 == 1

            if isinstance(origin, Vec2):
                period = num
                if mirror_subtree:
                    period -= 1
                subtree_rotation = ((2 * pi) / self.symmetry) * period

                if mirror_subtree:
                    subtree_rotation = (-subtree_rotation) + pi
            else:
                subtree_rotation = subtree[-1].rotation
            subtree_rotation += rotation * (-1 if mirror_subtree else 1)

            subtree.append(Segment(origin, length, subtree_rotation, color))

    def segments(self) -> Generator[Segment]:
        for subtree in self.subtrees:
            for segment in subtree:
                yield segment

    @cached_property
    def radius(self) -> float:
        return max(self.root.distance(s.destination) for s in self.segments())
