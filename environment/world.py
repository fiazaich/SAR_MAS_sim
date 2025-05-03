# environment/world.py
from dataclasses import dataclass
from math import dist
from typing import Dict, Tuple, List

WORLD: "GridWorld | None" = None   # will be set by runner at startup

def set_world(w: "GridWorld") -> None:
    global WORLD
    WORLD = w                       # allows late binding

def manhattan(a: str, b: str) -> int:
    """Convenience wrapper so callers don’t need the WORLD instance."""
    if WORLD is None:
        raise RuntimeError("WORLD is not initialised — call set_world(...) first.")
    return WORLD.manhattan(a, b)

@dataclass(frozen=True)
class Coord:
    x: int
    y: int

class GridWorld:
    """
    Immutable description of the search-and-rescue area.
    Zones are named “Z<row>_<col>”, e.g. Z3_7.
    """
    def __init__(self, width: int, height: int):
        self.width  = width
        self.height = height
        self.zones: List[str] = [
            f"Z{r}_{c}" for r in range(height) for c in range(width)
        ]
        self.zone_coord: Dict[str, Coord] = {
            z: Coord(int(z.split('_')[0][1:]), int(z.split('_')[1]))
            for z in self.zones
        }

    # ---------- helpers ----------
    def coord(self, zone: str) -> Coord:
        return self.zone_coord[zone]

    def manhattan(self, a: str, b: str) -> int:
        ca, cb = self.coord(a), self.coord(b)
        return abs(ca.x - cb.x) + abs(ca.y - cb.y)

    def neighbours(self, zone: str, r: int = 1) -> List[str]:
        """All zones within Manhattan radius *r* (inclusive)."""
        cz = self.coord(zone)
        return [
            z for z, c in self.zone_coord.items()
            if self.manhattan(zone, z) <= r and z != zone
        ]
