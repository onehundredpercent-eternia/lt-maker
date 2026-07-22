"""
PROTOTYPE -- CSP-based mountain group solver.

An alternative to AlgorithmXProcess (exact-cover / dancing-links) in
mountain_processing.py. Same problem: assign each mountain tile in a connected
group a tile-coord so that (a) its border edges match the group boundary and
(b) every adjacent pair is compatible per mountain_data.

Why a CSP instead of exact-cover: the exact-cover encoding balloons to
thousands of "invalid-coord" secondary columns whose cover/uncover cost
dominates on large groups. A direct CSP keeps one small domain per tile
(<= number of mountain tiles) and does forward-checking propagation in
O(domain) per neighbor -- attacking the measured hotspot directly.

NOT wave-function-collapse: variable order is MRV and *value* selection is
weighted-random by partner counts (the same signal NaiveBacktrackingProcess
uses), so the tile-frequency distribution is preserved rather than collapsing
to WFC's chaotic min-entropy output.

Interface mirrors AlgorithmXProcess so it can be swapped into MountainPainter:
  __init__(tilemap, mountain_data, noneless_rules, group, gui_processing, waiting_callback)
  process_group(); attrs organization, did_complete, broke_out; stop().
"""
from typing import Callable, Dict, List, Optional, Set, Tuple
from collections import deque
import random

_OPPOSITE = {'right': 'left', 'left': 'right', 'up': 'down', 'down': 'up'}

from app.utilities.typing import Pos


class CSPProcess:
    def __init__(self, tilemap, mountain_data, noneless_rules,
                 group: Set[Pos], gui_processing: bool = True,
                 waiting_callback: Optional[Callable] = None):
        self.tilemap = tilemap
        self.mountain_data = mountain_data
        self.noneless_rules = noneless_rules
        self.group: Set[Pos] = group
        self.gui_processing = gui_processing
        self.waiting_callback = waiting_callback

        # Sort top-left to bottom-right (matches AlgorithmXProcess ordering)
        self.to_process = sorted(self.group, key=lambda x: (x[0] + x[1], x[0]))
        self.organization: Dict[Pos, Pos] = {}

        self.did_complete = False
        self.broke_out = False

        # Precomputed compatibility sets per coord (keys only, None already
        # stripped in noneless_rules). RIGHT[c] = coords allowed to the right
        # of c, etc.
        self._right: Dict[Pos, Set[Pos]] = {}
        self._left: Dict[Pos, Set[Pos]] = {}
        self._up: Dict[Pos, Set[Pos]] = {}
        self._down: Dict[Pos, Set[Pos]] = {}
        for coord, rules in self.noneless_rules.items():
            self._right[coord] = set(rules['right'].keys())
            self._left[coord] = set(rules['left'].keys())
            self._up[coord] = set(rules['up'].keys())
            self._down[coord] = set(rules['down'].keys())

        self.counter = 0
        self.step_limit = int(2e6)

    def stop(self):
        self.broke_out = True

    # ------------------------------------------------------------------ solve
    def process_group(self):
        print("--- Process CSP Group --- %d" % id(self))
        self.did_complete = False
        self.broke_out = False
        self.organization.clear()
        self.counter = 0

        positions = self.to_process
        domains: Dict[Pos, List[Pos]] = {pos: list(self.find_valid_coords(pos)) for pos in positions}
        domains = {pos: set(v) for pos, v in domains.items()}

        # Neighbors that live inside the group, with the direction FROM this
        # tile TO the neighbor. Used for forward checking.
        neighbors: Dict[Pos, List[Tuple[Pos, str]]] = {}
        group = self.group
        for pos in positions:
            x, y = pos
            nb = []
            if (x + 1, y) in group:
                nb.append(((x + 1, y), 'right'))
            if (x - 1, y) in group:
                nb.append(((x - 1, y), 'left'))
            if (x, y + 1) in group:
                nb.append(((x, y + 1), 'down'))
            if (x, y - 1) in group:
                nb.append(((x, y - 1), 'up'))
            neighbors[pos] = nb
        self._neighbors = neighbors

        assignment: Dict[Pos, Pos] = {}
        unassigned: Set[Pos] = set(positions)

        # Make the whole network arc-consistent up front, then maintain it
        # incrementally during search (MAC). Forward-checking alone only looks
        # one hop and thrashes; AC-3 propagates constraints transitively so
        # dead-ends surface far earlier and the search barely backtracks.
        if not self._ac3(list(self._all_arcs(positions)), domains, trail=[]):
            print("CSP: unsatisfiable after initial AC-3", flush=True)
            return

        ok = self._search(unassigned, domains, assignment)
        if self.broke_out:
            return
        if ok:
            self.organization.update(assignment)
            self.did_complete = True
            print("CSP solution found in %d steps" % self.counter, flush=True)
        else:
            print("CSP: no valid solution (%d steps)" % self.counter, flush=True)

    def _allowed(self, val: Pos, direction: str) -> Set[Pos]:
        # Coords allowed for a neighbor lying `direction` of a tile assigned val.
        if direction == 'right':
            return self._right[val]
        if direction == 'left':
            return self._left[val]
        if direction == 'down':
            return self._down[val]
        return self._up[val]

    def _select_var(self, unassigned: Set[Pos], domains) -> Pos:
        # Minimum-remaining-values; deterministic tie-break by position.
        best = None
        best_size = 1 << 30
        for pos in unassigned:
            s = len(domains[pos])
            if s < best_size or (s == best_size and (best is None or pos < best)):
                best_size = s
                best = pos
        return best

    def _order_values(self, pos: Pos, domains, assignment) -> List[Pos]:
        # Weight each candidate coord by how strongly already-assigned neighbors
        # want it (partner counts), then take a deterministic weighted-random
        # ordering. Falls back to uniform weight 1 so every candidate appears.
        coords = domains[pos]
        md = self.mountain_data
        weighted: List[Pos] = []
        x, y = pos
        west = assignment.get((x - 1, y))
        north = assignment.get((x, y - 1))
        east = assignment.get((x + 1, y))
        south = assignment.get((x, y + 1))
        for c in coords:
            w = 1
            if west is not None:
                w += md[west]['right'].get(c, 0)
            if north is not None:
                w += md[north]['down'].get(c, 0)
            if east is not None:
                w += md[c]['right'].get(east, 0)
            if south is not None:
                w += md[c]['down'].get(south, 0)
            weighted.extend([c] * w)
        rng = random.Random(self.tilemap.seed + x * 1024 ** 2 + y * 1024)
        rng.shuffle(weighted)
        seen: Set[Pos] = set()
        order: List[Pos] = []
        for c in weighted:
            if c not in seen:
                seen.add(c)
                order.append(c)
        return order

    def _all_arcs(self, positions):
        for pos in positions:
            for npos, direction in self._neighbors[pos]:
                # arc (npos, pos): revise npos against pos, direction from npos
                yield (npos, pos, _OPPOSITE[direction])

    def _revise(self, xi: Pos, xj: Pos, direction: str, domains, trail) -> bool:
        # Remove from domain[xi] every value with no support in domain[xj].
        # `direction` is from xi toward xj; a value a at xi is supported iff
        # some coord that may sit `direction` of a is still in domain[xj].
        dj = domains[xj]
        di = domains[xi]
        removed = None
        for a in di:
            if not (self._allowed(a, direction) & dj):
                if removed is None:
                    removed = []
                removed.append(a)
        if removed:
            for a in removed:
                di.discard(a)
            trail.append((xi, set(removed)))
            return True
        return False

    def _ac3(self, arcs, domains, trail) -> bool:
        # arcs: iterable of (xi, xj, direction_xi_to_xj). Returns False if a
        # domain wiped out (caller undoes trail).
        queue = deque(arcs)
        neighbors = self._neighbors
        while queue:
            xi, xj, direction = queue.popleft()
            if self._revise(xi, xj, direction, domains, trail):
                if not domains[xi]:
                    return False
                for xk, dir_ik in neighbors[xi]:
                    if xk == xj:
                        continue
                    queue.append((xk, xi, _OPPOSITE[dir_ik]))
        return True

    def _search(self, unassigned: Set[Pos], domains, assignment) -> bool:
        if self.broke_out:
            return False
        self.counter += 1
        if self.counter > self.step_limit:
            self.broke_out = True
            return False
        if self.counter % 20000 == 0:
            if self.gui_processing and self.waiting_callback:
                self.waiting_callback()
            print("CSP still processing %d (%d)" % (self.counter, id(self)), flush=True)
        if not unassigned:
            return True

        pos = self._select_var(unassigned, domains)
        unassigned.discard(pos)
        for val in self._order_values(pos, domains, assignment):
            assignment[pos] = val
            trail = []
            # Collapse pos to {val}, recording the removal, then re-establish
            # arc consistency across the network from pos outward.
            di = domains[pos]
            removed_self = di - {val}
            if removed_self:
                di.difference_update(removed_self)
                trail.append((pos, removed_self))
            arcs = [(npos, pos, _OPPOSITE[d]) for npos, d in self._neighbors[pos]
                    if npos not in assignment]
            if self._ac3(arcs, domains, trail):
                if self._search(unassigned, domains, assignment):
                    return True
            for p, r in trail:
                domains[p] |= r
            del assignment[pos]
        unassigned.add(pos)
        return False

    # --------------------------------------------- domain / border (reused)
    # These mirror AlgorithmXProcess exactly so domains match its constraints.
    def find_valid_coords(self, pos) -> list:
        north, east, south, west = self.get_cardinal_terrain(pos)
        north_edge = not north
        south_edge = not south
        east_edge = not east
        west_edge = not west
        valid_coords = \
            [coord for coord, rules in self.mountain_data.items() if
             ((north_edge and None in rules['up']) or (not north_edge and self.noneless_rules[coord]['up'])) and
             ((south_edge and None in rules['down']) or (not south_edge and self.noneless_rules[coord]['down'])) and
             ((east_edge and None in rules['right']) or (not east_edge and self.noneless_rules[coord]['right'])) and
             ((west_edge and None in rules['left']) or (not west_edge and self.noneless_rules[coord]['left']))]
        orig_valid_coords = valid_coords[:]
        if not north_edge and not south_edge and not east_edge and not west_edge:
            valid_coords = \
                [coord for coord in valid_coords if
                 None not in self.mountain_data[coord]['up'] or
                 None not in self.mountain_data[coord]['down'] or
                 None not in self.mountain_data[coord]['left'] or
                 None not in self.mountain_data[coord]['right']]
        if not valid_coords:
            valid_coords = orig_valid_coords
        return valid_coords

    def get_cardinal_terrain(self, pos: Pos) -> Tuple[bool, bool, bool, bool]:
        north = pos[1] == 0 or self.get_terrain((pos[0], pos[1] - 1))
        east = pos[0] + 1 == self.tilemap.width or self.get_terrain((pos[0] + 1, pos[1]))
        south = pos[1] + 1 == self.tilemap.height or self.get_terrain((pos[0], pos[1] + 1))
        west = pos[0] == 0 or self.get_terrain((pos[0] - 1, pos[1]))
        return north, east, south, west

    def get_terrain(self, pos: Pos) -> bool:
        return pos in self.group
