import math

from dataclasses import dataclass

from app.constants import TILEWIDTH, TILEHEIGHT

@dataclass
class Hex:
    q: float = 0
    r: float = 0
    s: float = 0

    def __hash__(self):
        return hash((self.q, self.r, self.s))

    def __add__(self, other):
        return Hex(self.q + other.q, self.r + other.r, self.s + other.s)

    def __sub__(self, other):
        return Hex(self.q - other.q, self.r - other.r, self.s - other.s)

    def scale(self, k):
        self.q *= k
        self.r *= k
        self.s *= k

    def length(self) -> float:
        return (abs(self.q) + abs(self.r) + abs(self.s)) / 2

hex_directions = [Hex(1, 0, -1), Hex(1, -1, 0), Hex(0, -1, 1), Hex(-1, 0, 1), Hex(-1, 1, 0), Hex(0, 1, -1)]

def get_neighbors(h: Hex) -> list:
    return [h + direction for direction in hex_directions]

@dataclass
class Orientation:
    f0: float = 0
    f1: float = 0
    f2: float = 0
    f3: float = 0
    b0: float = 0
    b1: float = 0
    b2: float = 0
    b3: float = 0
    start_angle: float = 0

orientation_horizontal = Orientation(math.sqrt(3), math.sqrt(3) / 2, 0, 3 / 2, math.sqrt(3) / 3, -1 / 3, 0, 2 / 3, 0.5)
orientation_vertical = Orientation(3 / 2, 0, math.sqrt(3) / 2, math.sqrt(3), 2 / 3, 0, -1 / 3, math.sqrt(3) / 3, 0.0)

@dataclass
class Layout:
    orientation: Orientation = None
    size: tuple = None
    origin: tuple = None

def default_layout(size: float = 16):
    return Layout(orientation_horizontal, (size, size), (0, 0))

def calculate_distance(a: Hex, b: Hex) -> float:
    c = a - b
    return c.length()

def hex_round(h: Hex) -> Hex:
    qi = int(round(h.q))
    ri = int(round(h.r))
    si = int(round(h.s))
    q_diff = abs(qi - h.q)
    r_diff = abs(ri - h.r)
    s_diff = abs(si - h.s)
    if q_diff > r_diff and q_diff > s_diff:
        qi = -ri - si
    elif r_diff > s_diff:
        ri = -qi - si
    else:
        si = -qi - ri
    return Hex(qi, ri, si)

def hex_lerp(a: Hex, b: Hex, t: float) -> Hex:
    return Hex(a.q * (1 - t) + b.q * t, a.r * (1 - t) + b.r * t, a.s * (1 - t) + b.s * t)

def hex_linedraw(a: Hex, b: Hex) -> list:
    """
    Returns a list of the Hex points that can be used to draw a line between the two Hexes
    Use these Hex points to figure out what hexes you cross
    """
    n = calculate_distance(a, b)
    a_nudge = Hex(a.q + 1e-6, a.r + 1e-6, a.s - 2e-6)
    b_nudge = Hex(b.q + 1e-6, b.r + 1e-6, b.s - 2e-6)
    results = []
    step = 1.0 / max(n, 1)
    for i in range(n + 1):
        results.append(hex_round(hex_lerp(a_nudge, b_nudge, step * i)))
    return results

EVEN = 1
ODD = -1
def roffset_from_cube(offset, h: Hex) -> tuple:
    col = h.q + (h.r + offset * (h.r & 1)) // 2
    row = h.r
    if offset != EVEN and offset != ODD:
        raise ValueError("offset %s must be EVEN (+1) or ODD (-1)" % offset)
    return (col, row)

def roffset_to_cube(offset, h: tuple) -> Hex:
    q = h[0] - (h[1] + offset * (h[1] & 1)) // 2
    r = h[1]
    s = -q - r
    if offset != EVEN and offset != ODD:
        raise ValueError("offset %s must be EVEN (+1) or ODD (-1)" % offset)
    return Hex(q, r, s)

def _hex_to_pixel(layout: Layout, h: Hex) -> tuple:
    m = layout.orientation
    x = (m.f0 * h.q + m.f1 * h.r) * layout.size[0]
    y = (m.f2 * h.q + m.f3 * h.r) * layout.size[1]
    return (x + layout.origin[0], y + layout.origin[1])

def hex_to_pixel(h: Hex) -> tuple:
    return _hex_to_pixel(default_layout(), h)

def _pixel_to_hex(layout: Layout, p: tuple) -> Hex:
    m = layout.orientation
    pt = (p[0] - layout.origin[0]) / layout.size[0], (p[1] - layout.origin[1]) / layout.size[1]
    q = m.b0 * pt[0] + m.b1 * pt[1]
    r = m.b2 * pt[0] + m.b3 * pt[1]
    return Hex(q, r, -q - r)

def pixel_to_hex(h: Hex) -> tuple:
    return _pixel_to_hex(default_layout(), h)

def hex_corner_offset(layout: Layout, corner: int) -> tuple:
    m = layout.orientation
    size = layout.size
    angle = 2 * math.pi * (m.start_angle - corner) / 6.0
    return size[0] * math.cos(angle), size[1] * math.sin(angle)

def polygon_corners(layout: Layout, h: Hex) -> list:
    corners = []
    center = hex_to_pixel(layout, h)
    for i in range(6):
        offset = hex_corner_offset(layout, i)
        corners.append((center[0] + offset[0], center[1] + offset[1]))
    return corners

def get_all_hex_within_distance(h: Hex, dist: int) -> list:
    neighbors = []
    for q in range(-dist, dist + 1):
        for r in range(max(-dist, -q - dist), min(dist, -q + dist) + 1):
            s = -q - r
            neighbors.append(h.add(Hex(q, r, s)))
