from __future__ import annotations

import re
from collections.abc import Iterable
from functools import cached_property

DECIMAL_RANGE = (2 ** 8) ** 3


def _raw_hex_to_tuple(h: str) -> tuple[int, int, int]:
    h = h.rjust(6, "0")

    if len(h) != 6:
        raise ValueError()

    return tuple(int(x, 16) for x in re.findall(r"..", h))


class Color:
    def __init__(self, val):
        match val:
            case int():
                if val < 0:
                    val += DECIMAL_RANGE

                if val not in range(DECIMAL_RANGE):
                    raise ValueError()

                val = _raw_hex_to_tuple(f"{val:x}")

            case str():
                val = re.search(r"[\dA-F]{6}$", val, flags=re.IGNORECASE)
                if not val:
                    raise ValueError()
                val = _raw_hex_to_tuple(val.group())

            case Iterable():
                val = tuple(val)

                if len(val) != 3 or not all(isinstance(x, int) and x in range(256) for x in val):
                    raise ValueError()

            case _:
                raise TypeError()

        self._rgb: tuple[int, int, int] = val

    def __str__(self):
        return str(self.rgb)

    def __repr__(self):
        return f"<Color: {self}>"

    def __eq__(self, other: Color or tuple):
        match other:
            case Color():
                return self.rgb == other.rgb

            case tuple():
                return self.rgb == other

        raise TypeError()

    @property
    def rgb(self) -> tuple[int, int, int]:
        return self._rgb

    @property
    def r(self) -> int:
        return self.rgb[0]

    @property
    def g(self) -> int:
        return self.rgb[1]

    @property
    def b(self) -> int:
        return self.rgb[2]

    @property
    def name(self) -> str:
        return "unnamed color"

    @cached_property
    def html(self) -> str:
        colors = [f"{v:x}".rjust(2, "0").upper() for v in self.rgb]
        return f"#{''.join(colors)}"
