import random

# https://www.sbgames.org/sbgames2017/papers/ComputacaoFull/175350.pdf

class Automata:
    def __init__(self, size):
        self.width, self.height = size
        self.grid = [0] * (self.width * self.height)

    def get(self, grid: list, x: int, y: int) -> int:
        return grid[y * self.height + x]

    def set(self, grid: list, x: int, y: int, val: int) -> None:
        grid[y * self.height + x] = val

    def get_num_adj(self, grid: list, x: int, y: int) -> int:
        adj_list = [(x - 1, y - 1), (x, y - 1), (x + 1, y - 1),
                    (x - 1, y), (x + 1, y), 
                    (x - 1, y + 1), (x, y + 1), (x + 1, y + 1)]
        # Positions outside the grid count as True
        return len([adj for adj in adj_list if 
                    adj[0] < 0 or adj[0] >= self.width or 
                    adj[1] < 0 or adj[1] >= self.height or
                    self.get(grid, *adj)])

    def process(self):
        counter = 0
        while counter < 10:
            counter += 1
            new_grid = self.grid.copy()
            for y in range(self.height):
                for x in range(self.width):
                    num_adj = self.get_num_adj(self.grid, x, y)
                    if num_adj > 4:
                        self.set(new_grid, x, y, 1)
                    elif num_adj < 4:
                        self.set(new_grid, x, y, 0)
            self.grid = new_grid

    def randomize(self, chance=0.5):
        for idx in range(self.width * self.height):
            c = random.random()
            val = 1
            if c < chance:
                val = 0
            self.grid[idx] = val

    def print_grid(self):
        for y in range(self.height):
            print("%02d: " % y, end='')
            for x in range(self.width):
                val = self.get(self.grid, x, y)
                if val:
                    print(" ", end='')
                else:
                    print("X", end='')
            print("\n", end='')


if __name__ == '__main__':
    automata = Automata((20, 20))
    automata.randomize()
    automata.print_grid()
    automata.process()
    automata.print_grid()
