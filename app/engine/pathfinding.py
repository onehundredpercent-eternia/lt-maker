import heapq, random
from typing import Tuple, Callable

from app.utilities import utils

class Djikstra():
    __slots__ = ['open', 'closed', 'cells', 'bounds', 'height', 'start_pos',
                 'start_cell', 'unit_team', 'diagonal']

    def __init__(self, start_pos: tuple, grid: list, bounds: Tuple[int, int, int, int],
                 height: int, unit_team: str, diagonal: bool = False):
        self.open = []
        heapq.heapify(self.open)
        self.closed = set()
        self.cells = grid # Must keep order
        self.bounds: Tuple[int, int, int, int] = bounds
        self.diagonal = diagonal
        self.height = height
        self.reset_grid()
        self.start_pos = start_pos
        self.start_cell = self.get_cell(start_pos[0], start_pos[1])
        self.unit_team = unit_team

    def reset_grid(self):
        for cell in self.cells:
            cell.reset()

    def get_cell(self, x, y):
        return self.cells[x * self.height + y]

    def get_adjacent_cells(self, cell) -> list:
        if self.diagonal:
            return self.get_surrounding_cells(cell)
        return self.get_manhattan_adjacent(cell)

    def get_manhattan_adjacent(self, cell):
        cells = []
        if cell.y < self.bounds[3]:
            cells.append(self.get_cell(cell.x, cell.y + 1))
        if cell.x < self.bounds[2]:
            cells.append(self.get_cell(cell.x + 1, cell.y))
        if cell.x > self.bounds[0]:
            cells.append(self.get_cell(cell.x - 1, cell.y))
        if cell.y > self.bounds[1]:
            cells.append(self.get_cell(cell.x, cell.y - 1))
        return cells

    def get_surrounding_cells(self, cell):
        x = cell.x
        y = cell.y
        cells = []
        for i in range(-1, 2):
            for j in range(-1, 2):
                nx, ny = (x + i, y + j)
                if self.bounds[0] <= nx <= self.bounds[2] and self.bounds[1] <= ny <= self.bounds[3] and not (nx, ny) == (x, y):
                    cells.append(self.get_cell(nx, ny))
        return cells

    def update_cell(self, adj, cell):
        # g is true distance between this cell and starting position
        adj.g = cell.g + adj.cost
        adj.parent = cell

    def process(self, can_move_through: Callable, movement_left: float) -> set:
        # add starting cell to open heap queue
        heapq.heappush(self.open, (self.start_cell.g, self.start_cell))
        while self.open:
            # pop cell from heap queue
            g, cell = heapq.heappop(self.open)
            # If we've traveled too far -- always g ordered, so leaving at the
            # first sign of trouble will always work
            if g > movement_left:
                return {(cell.x, cell.y) for cell in self.closed}
            # add cell to closed set so we don't process it twice
            self.closed.add(cell)
            # get adjacent cells for cell
            adj_cells = self.get_adjacent_cells(cell)
            for adj in adj_cells:
                if adj.reachable and adj not in self.closed:
                    if can_move_through(self.unit_team, adj):
                        if (adj.g, adj) in self.open:
                            # if adj cell in open list, check if current path
                            # is better than the one previously found for this adj cell
                            if adj.g > cell.g + adj.cost:
                                self.update_cell(adj, cell)
                                heapq.heappush(self.open, (adj.g, adj))
                        else:
                            self.update_cell(adj, cell)
                            heapq.heappush(self.open, (adj.g, adj))
                    else:  # Unit is in the way
                        pass
        # Sometimes gets here if unit is enclosed
        return {(cell.x, cell.y) for cell in self.closed}

class AStar():
    def __init__(self, start_pos: tuple, goal_pos: tuple, grid: list,
                 bounds: Tuple[int, int, int, int], height: int, unit_team: str,
                 diagonal: bool = False):
        self.cells = grid
        self.bounds = bounds
        self.height = height
        self.start_pos = start_pos
        self.goal_pos = goal_pos
        self.diagonal = diagonal

        self.start_cell = self.get_cell(start_pos[0], start_pos[1])
        self.end_cell = self.get_cell(goal_pos[0], goal_pos[1]) if goal_pos else None
        self.adj_end = self.get_adjacent_cells(self.end_cell) if self.end_cell else None

        self.unit_team = unit_team

        self.reset()

    def reset_grid(self):
        for cell in self.cells:
            cell.reset()

    def reset(self):
        self.open = []
        heapq.heapify(self.open)
        self.closed = set()
        self.reset_grid()

    def set_goal_pos(self, goal_pos):
        self.goal_pos = goal_pos
        self.end_cell = self.get_cell(goal_pos[0], goal_pos[1])
        self.adj_end = self.get_adjacent_cells(self.end_cell)

    def get_heuristic(self, cell) -> float:
        """
        Compute the heuristic for this cell
        h is the approximate distance between this cell and the goal cell
        """
        # Get main heuristic
        dx1 = cell.x - self.end_cell.x
        dy1 = cell.y - self.end_cell.y
        h = abs(dx1) + abs(dy1)
        # Are we going in direction of goal?
        # Slight nudge in direction that lies along path from start to end
        dx2 = self.start_cell.x - self.end_cell.x
        dy2 = self.start_cell.y - self.end_cell.y
        cross = abs(dx1 * dy2 - dx2 * dy1)
        return h + cross * .001

    def get_simple_heuristic(self, cell) -> float:
        """
        Compute the heuristic for this cell
        h is the approximate distance between this cell and the goal cell
        """
        dx1 = cell.x - self.end_cell.x
        dy1 = cell.y - self.end_cell.y
        h = abs(dx1) + abs(dy1)
        return h

    def get_cell(self, x, y):
        return self.cells[x * self.height + y]

    def get_adjacent_cells(self, cell) -> list:
        if self.diagonal:
            return self.get_surrounding_cells(cell)
        return self.get_manhattan_adjacent(cell)

    def get_manhattan_adjacent(self, cell):
        cells = []
        if cell.y < self.bounds[3]:
            cells.append(self.get_cell(cell.x, cell.y + 1))
        if cell.x < self.bounds[2]:
            cells.append(self.get_cell(cell.x + 1, cell.y))
        if cell.x > self.bounds[0]:
            cells.append(self.get_cell(cell.x - 1, cell.y))
        if cell.y > self.bounds[1]:
            cells.append(self.get_cell(cell.x, cell.y - 1))
        return cells

    def get_surrounding_cells(self, cell):
        x, y = cell.x, cell.y
        cells = []
        for i in range(-1, 2):
            for j in range(-1, 2):
                nx, ny = (x + i, y + j)
                if self.bounds[0] <= nx <= self.bounds[2] and self.bounds[1] <= ny <= self.bounds[3] and not (nx, ny) == (x, y):
                    if (j != 0 and i != 0):
                        self.get_single_diagonal((x, ny), (nx, y), (nx, ny), cells)
                    else:
                        cells.append(self.get_cell(nx, ny))
        return cells

    def get_single_diagonal(self, vadj: tuple, hadj: tuple, diagonal: tuple, cells):
        if self.get_cell(vadj[0], vadj[1]).reachable and self.get_cell(hadj[0], hadj[1]).reachable:
            cells.append(self.get_cell(diagonal[0], diagonal[1]))

    def update_cell(self, adj, cell):
        # h is approximate distance between this cell and the goal
        # g is true distance between this cell and the starting position
        # f is simply them added together
        adj.g = cell.g + adj.cost
        adj.h = self.get_heuristic(adj)
        adj.parent = cell
        adj.f = adj.h + adj.g
        adj.true_f = self.get_simple_heuristic(adj) + adj.g

    def return_path(self, cell) -> list:
        path = []
        while cell:
            path.append((cell.x, cell.y))
            cell = cell.parent
        return path

    def process(self, can_move_through: Callable, adj_good_enough: bool = False,
                limit: float = None) -> list:
        # Add starting cell to open queue
        heapq.heappush(self.open, (self.start_cell.f, self.start_cell))
        while self.open:
            f, cell = heapq.heappop(self.open)
            # Make sure we don't process the cell twice
            self.closed.add(cell)
            # If this cell is past the limit, just return None
            # Uses f, not g, because g will cut off if first greedy path fails
            # f only cuts off if all cells are bad
            if limit is not None and cell.true_f > limit:
                return []
            # if ending cell, display found path
            if cell is self.end_cell or (adj_good_enough and cell in self.adj_end):
                return self.return_path(cell)
            # get adjacent cells for cell
            adj_cells = self.get_adjacent_cells(cell)
            for adj in adj_cells:
                if adj.reachable and adj not in self.closed:
                    if can_move_through(self.unit_team, adj):
                        if (adj.f, adj) in self.open:
                            # if adj cell in open list, check if current path
                            # is better than the one previously found for this adj cell
                            if adj.g > cell.g + adj.cost:
                                self.update_cell(adj, cell)
                                heapq.heappush(self.open, (adj.f, adj))
                        else:
                            self.update_cell(adj, cell)
                            heapq.heappush(self.open, (adj.f, adj))
                    else:  # Is blocked
                        pass
        return []

class MeanderingPathFinder:
    """
    Just finds a greedy meandering path that tries to ignore the goal as
    long as possible
    """

    class Node:
        def __init__(self, x, y, cost):
            self.x, self.y = x, y
            self.cost = cost
            self.parent = None

    def __init__(self, start_pos: tuple, goal_pos: tuple,
                 bounds: Tuple[int, int, int, int], keep_away_dist=3):
        self.bounds = bounds
        self.start_pos = start_pos
        self.goal_pos = goal_pos
        self.keep_away_dist = keep_away_dist

        self.reset()

    def reset_grid(self):
        self.grid = {}
        for x in range(self.bounds[0], self.bounds[2] + 1):
            for y in range(self.bounds[1], self.bounds[3] + 1):
                self.grid[(x, y)] = self.Node(x, y, 1)
        self.cost_path([self.goal_pos])

    def reset(self):
        self.open = []
        heapq.heapify(self.open)
        self.closed = set()
        self.reset_grid()

    def cost_path(self, path: list):
        for path_pos in path:
            for pos in self.grid:
                dist = utils.calculate_distance(path_pos, pos)
                if dist < self.keep_away_dist:
                    node = self.grid[pos]
                    new_cost = max(self.keep_away_dist - dist + 1, 1)
                    node.cost = max(new_cost, node.cost)

    def get_adjacent_pos(self, pos: tuple) -> list:
        cells = []
        x, y = pos
        if y < self.bounds[3]:
            cells.append((x, y + 1))
        if x < self.bounds[2]:
            cells.append((x + 1, y))
        if x > self.bounds[0]:
            cells.append((x - 1, y))
        if y > self.bounds[1]:
            cells.append((x, y - 1))
        random.shuffle(cells)
        return cells

    def update_cell(self, adj, cell):
        self.cost_path([adj])
        self.grid[adj].parent = cell

    def return_path(self, cell) -> list:
        path = []
        while cell:
            path.append((cell.x, cell.y))
            cell = cell.parent
        return path

    def process(self) -> list:
        # Add starting cell to open queue
        heapq.heappush(self.open, (self.grid[self.start_pos].cost, self.start_pos))
        counter = 0
        while self.open:
            counter += 1
            print(len(self.closed))
            if counter % 10:
                self.print_grid()
                input()

            cost, pos = heapq.heappop(self.open)
            self.closed.add(pos)
            if pos is self.goal_pos:
                return self.return_path(pos)
            adj_positions = self.get_adjacent_pos(pos)
            for adj in adj_positions:
                if adj not in self.closed:
                    self.update_cell(adj, pos)
                    heapq.heappush(self.open, (self.grid[adj].cost, adj))
        return []

    def print_grid(self):
        for y in range(self.bounds[1], self.bounds[3] + 1):
            print("%02d: " % y, end='')
            for x in range(self.bounds[0], self.bounds[2] + 1):
                print("%02d " % self.grid[(x, y)].cost, end='')
            print("\n", end='')

if __name__ == '__main__':
    pathfinder = MeanderingPathFinder((0, 0), (19, 19), (0, 0, 19, 19))
    pathfinder.print_grid()
    path = pathfinder.process()
    pathfinder.print_grid()
    print(path)
