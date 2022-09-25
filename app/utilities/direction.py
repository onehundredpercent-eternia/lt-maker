from enum import Enum

class Direction(str, Enum):
    CENTER = 'center'
    NORTH = 'north'
    EAST = 'east'
    SOUTH = 'south'
    WEST = 'west'
    NORTHEAST = 'northeast'
    SOUTHEAST = 'southeast'
    SOUTHWEST = 'southwest'
    NORTHWEST = 'northwest'

    @staticmethod
    def opposite(direction):
        if direction == Direction.NORTH:
            return Direction.SOUTH
        elif direction == Direction.SOUTH:
            return Direction.NORTH
        elif direction == Direction.EAST:
            return Direction.WEST
        elif direction == Direction.WEST:
            return Direction.EAST
        elif direction == Direction.NORTHEAST:
            return Direction.SOUTHWEST
        elif direction == Direction.SOUTHEAST:
            return Direction.NORTHWEST
        elif direction == Direction.SOUTHWEST:
            return Direction.NORTHEAST
        elif direction == Direction.NORTHWEST:
            return Direction.SOUTHEAST
        return None

    @staticmethod
    def sorting_key(direction, size):
        width, height = size
        if direction == Direction.CENTER:
            return lambda x: abs(x[0] - width/2.) + abs(x[1] - height/2.)
        elif direction == Direction.NORTH:
            return lambda x: abs(x[0] - width/2.) + x[1]
        elif direction == Direction.SOUTH:
            return lambda x: abs(x[0] - width/2.) + -x[1]
        elif direction == Direction.EAST:
            return lambda x: -x[0] + abs(x[1] - height/2.)
        elif direction == Direction.WEST:
            return lambda x: x[0] + abs(x[1] - height/2.)
        elif direction == Direction.SOUTHWEST:
            return lambda x: x[0] + -x[1]
        elif direction == Direction.NORTHEAST:
            return lambda x: -x[0] + x[1]
        elif direction == Direction.NORTHWEST:
            return lambda x: x[0] + x[1]
        elif direction == Direction.SOUTHEAST:
            return lambda x: -x[0] + -x[1]
        else:
            raise ValueError("%s is not a valid Direction" % direction)
