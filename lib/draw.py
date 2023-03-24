from __future__ import annotations

from PIL import ImageDraw, Image
from pyglet.math import Vec2
from typing import Generator
from functools import cached_property

from .datamodel import Organism, Clade
from .composite import WorldComposite, Species

DIAGRAM_COLOR = (169, 169, 169)
LINE_THICKNESS = 3

GENERATION_LINE_COLOR = (37, 63, 63)

EDGE_MARGIN = 25

BUBBLE_PADDING = 14
BUBBLE_MIN_RADIUS = 24
CONNECTOR_MARGIN = 45
SPECIES_MARGIN = 60
SPECIES_MIN_WIDTH = 80
GENERATION_MARGIN = 150
GENRATION_MIN_HEIGHT = 160

POPULATION_THRESHOLD = 10


class NoGenerationsError(ValueError):
    pass


class CladeDraw(ImageDraw.ImageDraw):
    def organism(self, xy: tuple[int, int], organism: Organism):
        for segment in organism.segment_tree.segments():
            self.line(segment.xy(Vec2(*xy)), segment.color.rgb)

    def connector(self, start: tuple[int, int], end: tuple[int, int], midrange: int):
        xy = (
            start,
            (start[0], midrange),
            (end[0], midrange),
            end
        )
        self.line(xy, DIAGRAM_COLOR, LINE_THICKNESS)

    def circle(self, xy: tuple[int, int], radius: float):
        xy = (
            (round(xy[0] - radius), round(xy[1] - radius)),
            (round(xy[0] + radius), round(xy[1] + radius))
        )
        self.ellipse(xy, outline=DIAGRAM_COLOR, fill=(0, 0, 0), width=LINE_THICKNESS)


def _aggregate_width(species: list[CladeSpecies]):
    bubbles = [s.diagram_element for s in species]
    return sum(b.base_width_allocation() for b in bubbles)


class DiagramBubble:
    def __init__(self, species: CladeSpecies):
        self.cspecies: CladeSpecies = species

        self._x = None

    @cached_property
    def x(self) -> int:
        # if (x := self._x) is not None:
        #     return x

        positions = []

        if (previous := self.previous()) is not None:
            positions.append(self._x_from(previous))

            if (own_child_count := self.cspecies.child_generation_count()) > 0:
                bubbles = []
                for species in self.cspecies.before():
                    for generation in species.child_generations(own_child_count):
                        bubbles.append(generation[-1].diagram_element)
                bubble = max(bubbles, key=lambda b: b.x)

                positions.append(self._x_from(bubble))

            # if (previous_parent := previous.cspecies.get_parent()) is not None \
            # and self.cspecies.get_parent() is not previous_parent:
            #     positions.append(previous_parent.diagram_element.x() + CONNECTOR_MARGIN)

            # previous_descendants_bubbles = [cg[-1].diagram_element for cg in previous.cspecies.child_generations()]
            # if previous_descendants_bubbles:
            #     bubble = max(previous_descendants_bubbles, key=lambda b: b.x())
            #     positions.append(self._x_from(bubble))
        else:
            positions.append(EDGE_MARGIN + self.radius)

        if (parent := self.cspecies.get_parent()) is not None:
            positions.append(parent.diagram_element.x)

        # self._x = max(positions)
        # return self._x
        return max(positions)

    @cached_property
    def y(self) -> int:
        return self.cspecies.generation.y_pos()

    @property
    def organism(self) -> Organism:
        return self.cspecies.species.representative

    @property
    def radius(self) -> int:
        return max(round(self.organism.radius) + BUBBLE_PADDING, BUBBLE_MIN_RADIUS)

    @property
    def diameter(self) -> int:
        return self.radius * 2

    def _heading(self, factor: int) -> tuple[int, int]:
        return (self.x, self.y + self.radius * factor)

    @property
    def top(self) -> tuple[int, int]:
        return self._heading(-1)

    @property
    def bottom(self) -> tuple[int, int]:
        return self._heading(1)

    @property
    def xy(self) -> tuple[int, int]:
        return (self.x, self.y)

    def previous(self) -> DiagramBubble or None:
        if (previous_species := self.cspecies.previous()) is not None:
            return previous_species.diagram_element

        return None

    def base_width_allocation(self) -> int:
        return max(self.diameter + SPECIES_MARGIN, SPECIES_MIN_WIDTH)

    @cached_property
    def _column_radius(self):
        radii = [self.radius]
        radii += [cg[0].diagram_element.radius for cg in self.cspecies.child_generations()]
        return max(radii)

    def _x_from(self, other: DiagramBubble):
        return other.x + other.base_width_allocation() - other.radius + self._column_radius

    def draw(self, surface: CladeDraw):
        species = self.cspecies
        representative = species.representative
        if len(children := species.get_children()) == 1 \
        and (parent := species.get_parent()) is not None \
        and len(parent.get_children()) == 1 \
        and representative == parent.representative \
        and representative == children[0].representative:
            surface.connector(self.bottom, self.top, self.y)
            return

        surface.circle(self.xy, self.radius)
        surface.organism(self.xy, self.cspecies.representative)

    def draw_connector(self, surface: CladeDraw, to: DiagramBubble):
        midrange = self.cspecies.generation.midpoint(to.cspecies.generation)
        surface.connector(self.top, to.bottom, midrange)


class CladeSpecies:
    def __init__(self, generation: CladeGeneration, species: Species):
        self.generation: CladeGeneration = generation
        self.species: Species = species
        self.diagram_element = DiagramBubble(self)

        self._parent: CladeSpecies or None = None

        self._children: list[CladeSpecies] or None
        self._child_generation_count: int or None
        self._reset_cache()

    def _reset_cache(self):
        self._children = None
        self._child_generation_count = None

    @property
    def clade(self) -> Clade:
        return self.species.clade

    @property
    def representative(self) -> Organism:
        return self.species.representative

    @property
    def population(self) -> int:
        return self.species.population

    def get_index(self) -> int:
        return self.generation.species.index(self)

    def before(self) -> list[CladeSpecies]:
        return self.generation.species[:self.get_index()]

    def after(self) -> list[CladeSpecies]:
        return self.generation.species[self.get_index() + 1:]

    def previous(self) -> CladeSpecies or None:
        if before := self.before():
            return before[-1]

        return None

    def next(self) -> CladeSpecies or None:
        if after := self.after():
            return after[0]

        return None

    def get_parent(self) -> CladeSpecies or None:
        if (parent := self._parent) is not None:
            return parent

        if (previous_generation := self.generation.previous()) is None:
            return None

        candidates = [s for s in previous_generation.species if self.clade.is_direct_ancestor(s.clade)]

        if not candidates:
            return None

        candidates.sort(key=lambda s: self.clade.distance_from(s.clade))
        self._parent = candidates[0]
        return self._parent

    def get_children(self) -> list[CladeSpecies]:
        if (children := self._children) is not None:
            return children

        if (next_generation := self.generation.next()) is None:
            return []

        self._children = [s for s in next_generation.species if s.get_parent() is self]
        return self._children

    def child_generations(self, stop: int or None = None) -> Generator[list[CladeSpecies]]:
        generation = [self]
        i = 0
        while True:
            if i == stop:
                break

            next_generation = []
            for species in generation:
                next_generation += species.get_children()
            generation = next_generation

            if not generation:
                break

            yield generation

            i += 1

    def child_generation_count(self) -> int:
        if (count := self._child_generation_count) is not None:
            return count

        self._child_generation_count = len(list(self.child_generations()))
        return self._child_generation_count

    def should_include(self) -> bool:
        if self.population >= POPULATION_THRESHOLD:
            return True

        if (parent := self.get_parent()) is not None:
            if parent.clade == self.clade and parent.should_include():
                return True

        for generation in self.child_generations():
            if sum(s.population for s in generation) >= POPULATION_THRESHOLD:
                return True

        return False


def _sorted_by_child_count(l: list[CladeSpecies]):
    l = sorted(l, key=lambda s: s.child_generation_count())
    return l[-1:] + l[:-1]


class CladeGeneration:
    def __init__(self, diagram: CladeDiagram, species: list[Species]):
        self.diagram: CladeDiagram = diagram

        self.species: list[CladeSpecies] = [CladeSpecies(self, s) for s in species]

    def _reset_cache(self):
        for species in self.species:
            species._reset_cache()

    def _post_update1(self):
        self.species = [s for s in self.species if s.should_include()]

    def _post_update2(self):
        # TODO: More advanced space optimization

        if (previous_generation := self.previous()) is not None:
            updated_species = []
            previous_species = previous_generation.species
            for species in previous_species:
                updated_species += _sorted_by_child_count(species.get_children())
            updated_species += _sorted_by_child_count([s for s in self.species if s not in updated_species])

            self.species = updated_species

    def add_species(self, species: CladeSpecies):
        self.species.append(species)

    def get_index(self):
        for i, generation in enumerate(self.diagram.generations):
            if generation is self:
                return i

    def after(self) -> list[CladeGeneration]:
        return self.diagram.generations[self.get_index() + 1:]

    def before(self) -> list[CladeGeneration]:
        return self.diagram.generations[:self.get_index()]

    def next(self) -> CladeGeneration or None:
        after = self.after()
        return after[0] if after else None

    def previous(self) -> CladeGeneration or None:
        before = self.before()
        return before[-1] if before else None

    def height(self) -> int:
        if not self.species:
            return BUBBLE_MIN_RADIUS * 2

        return max(s.diagram_element.diameter for s in self.species)

    def width(self) -> int:
        if not self.species:
            return BUBBLE_MIN_RADIUS * 2 + EDGE_MARGIN * 2

        last_bubble = self.species[-1].diagram_element
        return last_bubble.x + last_bubble.radius + EDGE_MARGIN

    def y_pos(self) -> int:
        y = EDGE_MARGIN
        y += sum(max(g.height() + GENERATION_MARGIN, GENRATION_MIN_HEIGHT) for g in self.after())
        y += self.height() / 2
        return y

    def midpoint(self, other: CladeGeneration) -> int:
        self_y = self.y_pos()
        return round(self_y + (other.y_pos() - self_y) / 2)


class CladeDiagram:
    def __init__(self, generation_worlds: list[WorldComposite]):
        if not generation_worlds:
            raise NoGenerationsError()

        print("Initializing clade...")
        self.generations: list[CladeGeneration] = [CladeGeneration(self, w.species) for w in generation_worlds]

        for generation in self.generations:
            generation._post_update1()
        self._reset_cache()
        for generation in self.generations:
            generation._post_update2()
        self._reset_cache()

        print("Completed clade diagram initialization.")

    def _reset_cache(self):
        for generation in self.generations:
            generation._reset_cache()

    def add_generation(self, generation: CladeGeneration):
        self.generations.append(generation)

    @cached_property
    def width(self) -> int:
        return max(g.width() for g in self.generations)

    @cached_property
    def height(self) -> int:
        height = sum(max(g.height() + GENERATION_MARGIN, GENRATION_MIN_HEIGHT) for g in self.generations[:-1])
        height += self.generations[-1].height()
        height += EDGE_MARGIN * 2
        return height

    def bubbles(self) -> Generator[DiagramBubble]:
        for generation in self.generations:
            for species in generation.species:
                yield species.diagram_element

    def render_to_file(self, path):
        print("Initializing image...")
        image = Image.new("RGB", (self.width, self.height), (0, 0, 0))
        draw = CladeDraw(image)

        print("Drawing generation lines...")
        for generation in self.generations:
            y = generation.y_pos()
            draw.line((0, y, self.width, y), GENERATION_LINE_COLOR)

        bubbles = list(self.bubbles())
        bubbles_count = len(bubbles)

        print("Drawing diagram connectors...")
        for i, bubble in enumerate(bubbles):
            if i % 100 == 0:
                print(f"Drawing connectors... ({i}/{bubbles_count})")

            for child in bubble.cspecies.get_children():
                bubble.draw_connector(draw, child.diagram_element)

        print("Drawing species bubbles...")
        for i, bubble in enumerate(bubbles):
            if i % 100 == 0:
                print(f"Drawing organisms... ({i}/{bubbles_count})")

            bubble.draw(draw)

        print("Writing clade.png...")
        image.save(path)
