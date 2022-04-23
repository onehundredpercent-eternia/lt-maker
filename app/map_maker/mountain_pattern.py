from enum import Enum

class MountainCategory(Enum):
    LIGHT = 1
    LIGHT_BRIGHT = 2
    LIGHT_TRANSITION = 3
    DARK = 4
    RIDGE = 5
    RIDGE_BRIGHT = 6
    RIDGE_TRANSITION = 7
    VALLEY = 8
    LIGHT_RARE = 9
    LIGHT_BRIGHT_RARE = 10

class MountainPattern():
    def __init__(self, coord, edges, category, ridges=None):
        self.coord: tuple = coord  # Position on tilemap
        self.category: MountainCategory = category
        self.edges: tuple = edges if edges else tuple()  # tuple containing 1 through 8
        self.ridges: list = ridges or tuple()

    @property
    def top_edge(self) -> bool:
        return 1 in self.edges and 8 in self.edges

    @property
    def bottom_edge(self) -> bool:
        return 4 in self.edges and 5 in self.edges
    
    @property
    def left_edge(self) -> bool:
        return 6 in self.edges and 7 in self.edges

    @property
    def right_edge(self) -> bool:
        return 2 in self.edges and 3 in self.edges

    def edge_match(self, top_edge: bool, left_edge: bool, bottom_edge: bool, right_edge: bool) -> bool:
        if top_edge and not self.top_edge:
            return False
        if bottom_edge and not self.bottom_edge:
            return False
        if left_edge and not self.left_edge:
            return False
        if right_edge and not self.right_edge:
            return False

        edge_sum = sum((top_edge, left_edge, bottom_edge, right_edge))
        if edge_sum == 0 and len(self.edges) > 0:
            return False
        if edge_sum == 1 and len(self.edges) > 4:
            return False
        return True

    def category_match(self, pattern, direction: tuple) -> bool:
        x, y = direction

        # Find the valid categories
        valid_categories = (MountainCategory.DARK, MountainCategory.LIGHT)
        if self.category == MountainCategory.LIGHT:
            valid_categories = (MountainCategory.LIGHT,)
        elif self.category == MountainCategory.DARK:
            valid_categories = (MountainCategory.DARK,)
        elif self.category == MountainCategory.RIDGE:
            if x == 1 and y == 0:
                valid_categories = (MountainCategory.DARK,)
            elif x == -1 and y == 0:
                valid_categories = (MountainCategory.LIGHT,)
        elif self.category == MountainCategory.VALLEY:
            if x == 1 and y == 0:
                valid_categories = (MountainCategory.LIGHT,)
            elif x == -1 and y == 0:
                valid_categories = (MountainCategory.DARK,)

        return pattern.category in valid_categories

    def pattern_edge_match(self, pattern, direction: tuple) -> bool:
        x, y = direction
        if x == 1 and y == 0:
            match1 = bool(2 in self.edges) == bool(7 in pattern.edges)
            match2 = bool(3 in self.edges) == bool(6 in pattern.edges)
            return match1 and match2
        elif x == -1 and y == 0:
            match1 = bool(6 in self.edges) == bool(3 in pattern.edges)
            match2 = bool(7 in self.edges) == bool(2 in pattern.edges)
            return match1 and match2
        elif y == 1 and x == 0:
            match1 = bool(4 in self.edges) == bool(1 in pattern.edges)
            match2 = bool(5 in self.edges) == bool(8 in pattern.edges)
            return match1 and match2
        elif y == -1 and x == 0:
            match1 = bool(1 in self.edges) == bool(4 in pattern.edges)
            match2 = bool(8 in self.edges) == bool(5 in pattern.edges)
            return match1 and match2
        return True

    def ridge_match(self, pattern, direction: tuple) -> bool:
        """
        For determing whether these two patterns (self and pattern)
        match in the chosen direction
        """
        x, y = direction
        match = False
        if x == 0 and y == -1:  # up, 1
            match = bool(1 in self.ridges) == bool(5 in pattern.ridges)
            match &= bool(2 in self.ridges) == bool(4 in pattern.ridges)
            match &= bool(8 in self.ridges) == bool(6 in pattern.ridges)
        elif x == 1 and y == -1:  # upright, 2
            match = bool(2 in self.ridges) == bool(6 in pattern.ridges)
        elif x == 1 and y == 0:  # right, 3
            match = bool(3 in self.ridges) == bool(7 in pattern.ridges)
            match &= bool(2 in self.ridges) == bool(8 in pattern.ridges)
            match &= bool(4 in self.ridges) == bool(6 in pattern.ridges)
        elif x == 1 and y == 1:  # downright, 4
            match = bool(4 in self.ridges) == bool(8 in pattern.ridges)
        elif x == 0 and y == 1:  # down, 5
            match = bool(5 in self.ridges) == bool(1 in pattern.ridges)
            match &= bool(4 in self.ridges) == bool(2 in pattern.ridges)
            match &= bool(6 in self.ridges) == bool(8 in pattern.ridges)
        elif x == -1 and y == 1:  # downleft, 6
            match = bool(6 in self.ridges) == bool(2 in pattern.ridges)
        elif x == -1 and y == 1:  # left, 7
            match = bool(7 in self.ridges) == bool(3 in pattern.ridges)
            match &= bool(6 in self.ridges) == bool(4 in pattern.ridges)
            match &= bool(8 in self.ridges) == bool(2 in pattern.ridges)
        elif x == -1 and y == -1:  # upleft, 8
            match = bool(8 in self.ridges) == bool(4 in pattern.ridges)
        return match

    def ridge_connects(self, direction: tuple) -> bool:
        """
        For determining whether this pattern could possibly
        connect in the given direction
        """
        x, y = direction
        match = False
        if x == 0 and y == -1:  # up, 1
            match = bool(1 in self.ridges) or bool(2 in self.ridges) or bool(0 in self.ridges)
        elif x == 1 and y == -1:  # upright, 2
            match = bool(2 in self.ridges)
        elif x == 1 and y == 0:  # right, 3
            match = bool(3 in self.ridges) or bool(2 in self.ridges) or bool(4 in self.ridges)
        elif x == 1 and y == 1:  # downright, 4
            match = bool(4 in self.ridges)
        elif x == 0 and y == 1:  # down, 5
            match = bool(5 in self.ridges) or bool(4 in self.ridges) or bool(6 in self.ridges)
        elif x == -1 and y == 1:  # downleft, 6
            match = bool(6 in self.ridges)
        elif x == -1 and y == 1:  # left, 7
            match = bool(7 in self.ridges) or bool(6 in self.ridges) or bool(8 in self.ridges)
        elif x == -1 and y == -1:  # upleft, 8
            match = bool(8 in self.ridges)
        return match

    def matches(self, pattern, direction: tuple) -> bool:
        # direction is a 2-tuple that contains x, y direction for checking pattern
        if self.category_match(pattern, direction):
            pass
        else:
            return False

        if self.pattern_edge_match(pattern, direction):
            pass
        else:
            return False

        return True
