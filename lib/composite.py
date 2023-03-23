from __future__ import annotations

from .datamodel import World, Organism, Clade


class Subspecies:
    def __init__(self, data: Organism or dict):
        self._representative: Organism
        self._population: int

        if isinstance(data, Organism):
            self._representative = data
            self._population = 1
        else:
            self._representative = Organism(data["representative"])
            self._population = data["population"]

    def __eq__(self, other):
        match other:
            case Subspecies():
                return self.representative == other.representative

            case Organism():
                return self.representative == other

            case _:
                return NotImplemented

    @property
    def representative(self) -> Organism:
        return self._representative

    @property
    def population(self) -> int:
        return self._population

    @property
    def clade(self) -> Clade:
        return self.representative.clade

    def tally(self, count=1):
        self._population += count

    def to_data_dict(self):
        return {
            "representative": self.representative.pack(),
            "population": self.population
        }

    def copy(self) -> Subspecies:
        return Subspecies(self.to_data_dict())


class Species:
    def __init__(self, data: Clade or dict):
        self._clade: Clade
        self._subspecies: list[Subspecies]

        if isinstance(data, Clade):
            self._clade = data
            self._subspecies = []
        else:
            self._clade = Clade(data["clade"])
            self._subspecies = [Subspecies(sd) for sd in data["subspecies"]]

    @property
    def subspecies(self) -> list[Subspecies]:
        return sorted(self._subspecies, key=lambda s: s.population, reverse=True)

    @property
    def representative(self) -> Organism or None:
        representative_subspecies = self._subspecies
        if representative_subspecies:
            return representative_subspecies[0].representative
        else:
            return None

    @property
    def clade(self) -> Clade:
        return self._clade

    @property
    def population(self) -> int:
        return sum(s.population for s in self.subspecies)

    @property
    def subspecies_count(self) -> int:
        return len(self.subspecies)

    def log_subspecies(self, organism: Subspecies or Organism):
        if not isinstance(organism, (Subspecies, Organism)):
            raise TypeError()

        if organism.clade != self.clade:
            return False

        existing_subspecies = next((s for s in self.subspecies if s == organism), None)
        if existing_subspecies is not None:
            count = 1
            if isinstance(organism, Subspecies):
                count = organism.population

            existing_subspecies.tally(count)
        else:
            match organism:
                case Organism():
                    self._subspecies.append(Subspecies(organism))

                case Subspecies():
                    self._subspecies.append(organism.copy())

        return True

    def to_data_dict(self) -> dict:
        return {
            "clade": self.clade.string,
            "subspecies": [s.to_data_dict() for s in self.subspecies]
        }

    def copy(self) -> Species:
        return Species(self.to_data_dict())


class SpeciesIndex:
    def __init__(self, data: dict = None):
        self._species: dict[str, Species]
        self._species = {c: Species(s) for c, s in data.items()} if data is not None else {}

    @property
    def species(self) -> list[Species]:
        return list(self._species.values())

    @property
    def dict(self) -> dict[str, Species]:
        return self._species.copy()

    @property
    def population(self) -> int:
        return sum(s.population for s in self.species)

    @property
    def species_count(self) -> int:
        return len(self.species)

    @property
    def total_subspecies(self) -> int:
        return sum(s.subspecies_count for s in self.species)

    def log_organism(self, organism: Organism or Species or Subspecies):
        if not isinstance(organism, Organism):
            if isinstance(organism, (Species, Subspecies)):
                raise NotImplementedError()

            raise TypeError()

        clade = organism.clade
        species = self._species.setdefault(clade.string, Species(clade))
        species.log_subspecies(organism)

    def to_data_dict(self) -> dict:
        return {c: s.to_data_dict() for c, s in self.dict.items()}


class WorldComposite:
    def __init__(self, data: World or dict):
        self._species_index: SpeciesIndex
        self._time: int
        self.from_bgw: bool

        if isinstance(data, World):
            self.from_bgw = True

            self._species_index = SpeciesIndex()
            for organism in data.organisms:
                if not organism.alive:
                    continue

                self._species_index.log_organism(organism)
            self._time = data.time
        else:
            self.from_bgw = False

            self._species_index = SpeciesIndex(data["species"])
            self._time = data["time"]

    @property
    def time(self) -> int:
        return self._time

    @property
    def species_index(self) -> SpeciesIndex:
        return self._species_index

    @property
    def species(self) -> list[Species]:
        return self.species_index.species

    def to_data_dict(self) -> dict:
        return {
            "time": self.time,
            "species": self.species_index.to_data_dict()
        }
