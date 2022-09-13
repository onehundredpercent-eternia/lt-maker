from collections import Counter

from app.engine import engine

def read_image(image_fn):
    im = engine.image_load(image_fn)
    return im

def make_tile_catalog(image):
    """
    Takes an image and returns the following
    tile_grid is dictionary of the original image
    code_list is the original image in 1 dimension list
    unique_tiles is the set of tiles, plus the frequency of their occurence
    """
    width, height = image.get_width(), image.get_height()

    tile_grid = {}
    code_list = []
    for x in range(width):
        for y in range(height):
            r, g, b = image.get_color((x, y))
            tile_grid[(x, y)] = (r, g, b)
            code_list.append((r, g, b))

    unique_tiles = Counter()
    for pos, color in code_list:
        unique_tiles[color] += 1
    
    return tile_grid, code_list, unique_tiles



def solve(adjacencies, wave_matrix):
    contradiction = False
    while not contradiciton:
        wave_matrix = propagate(wave_matrix, adjacencies)
        if all_domains_collapsed:
            return wave_matrix
        wave_matrix = observe(wave_matrix)
    throw ValueError("Resource Generation Failed")

def observe(wave_matrix):
    """
    Finds the most constrained variable and picks a value to assign
    """
    # Find the minimum entropy cell in grid
    cell = find_minimum_entropy(wave_matrix)
    if all(cell.entropy == 0 for cell in wave_matrix):
        # We are done
        return wave_matrix
    cell.value = get_value(cell)
    propagation_stack.append(cell)

def propagate(wave_matrix, adjacencies):
    """
    Update the domain of variables at each grid location
    """
