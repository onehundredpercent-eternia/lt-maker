from collections import Counter

from PyQt5.QtGui import QImage

from app.editor.tile_editor.autotiles import PaletteData

from app.constants import TILEWIDTH, TILEHEIGHT

DIRECTIONS = ('left', 'right', 'up', 'down')

class QuadPaletteData():
    def __init__(self, im: QImage):
        topleft_rect = (0, 0, TILEWIDTH//2, TILEHEIGHT//2)
        self.topleft = PaletteData(im.copy(*topleft_rect))
        topright_rect = (TILEWIDTH//2, 0, TILEWIDTH//2, TILEHEIGHT//2)
        self.topright = PaletteData(im.copy(*topright_rect))
        bottomleft_rect = (0, TILEHEIGHT//2, TILEWIDTH//2, TILEHEIGHT//2)
        self.bottomleft = PaletteData(im.copy(*bottomleft_rect))
        bottomright_rect = (TILEWIDTH//2, TILEHEIGHT//2, TILEWIDTH//2, TILEHEIGHT//2)
        self.bottomright = PaletteData(im.copy(*bottomright_rect))

class MountainQuadPaletteData(QuadPaletteData):
    def __init__(self, im: QImage, coord: tuple):
        super().__init__(im)
        self.coord = coord
        self.rules = {}
        for direction in DIRECTIONS:
            self.rules[direction] = Counter()

def similar(p1: QuadPaletteData, p2: MountainQuadPaletteData, must_match=4) -> bool:

    def similar_fast(p1: list, p2: list) -> int:
        """
        Attempts to compare the pattern of the tiles, not the actual values themselves
        """
        mapping_to = {}
        mapping_fro = {}
        for i, j in zip(p1, p2):
            if i == j:
                mapping_to[i] = j
                mapping_fro[j] = i
            elif (i in mapping_to and j != mapping_to[i]) or (j in mapping_fro and i != mapping_fro[j]):
                return TILEWIDTH * TILEHEIGHT
            else:
                mapping_to[i] = j
                mapping_fro[j] = i
        return 0

    topleft_similar = similar_fast(p1.topleft.palette, p2.topleft.palette) == 0
    topright_similar = similar_fast(p1.topright.palette, p2.topright.palette) == 0
    bottomleft_similar = similar_fast(p1.bottomleft.palette, p2.bottomleft.palette) == 0
    bottomright_similar = similar_fast(p1.bottomright.palette, p2.bottomright.palette) == 0
    num_match = sum((topleft_similar, topright_similar, bottomleft_similar, bottomright_similar))
    return num_match >= must_match

def get_mountain_coords(fn) -> set:
    if fn.endswith('main.png'):
        topleft = {(0, 11), (0, 12), (1, 11), (1, 12), (1, 12), (2, 12), (3, 11), (3, 12)}
        main = {(x, y) for x in range(17) for y in range(13, 20)}
        # (18, 18) is a duplicate of (15, 17)
        right = {(17, 14), (17, 15), (17, 16), (17, 17), (17, 18), (17, 19), (18, 16), (18, 17), (18, 19)}
        bottomleft = {(4, 22), (5, 22), (0, 26), (0, 27), (0, 28), (1, 26), (1, 27), (2, 27), (3, 27)}
        bottom = {(x, y) for x in range(6, 12) for y in range(20, 25)}
        bottomright = {(12, 22), (13, 22), (14, 22), (15, 22), (12, 23), (13, 23), (14, 23), (15, 23), (16, 23), (12, 24), (13, 24), (13, 25), (15, 20), (16, 20), (17, 20), (18, 20), (17, 21), (18, 21)}
        # extra = {(0, 6), (1, 6), (2, 6)}
        extra = {(0, 5), (14, 21)}
        return topleft | main | right | bottomleft | bottom | bottomright | extra
    return set()

def load_mountain_palettes(fn, coords) -> dict:
    palettes = {}
    image = QImage(fn)
    for coord in coords:
        rect = (coord[0] * TILEWIDTH, coord[1] * TILEHEIGHT, TILEWIDTH, TILEHEIGHT)
        palette = image.copy(*rect)
        d = MountainQuadPaletteData(palette, coord)
        palettes[coord] = d
    return palettes

def assign_rules(palette_templates: dict, fns: list):
    print("Assign Rules")
    for fn in fns:
        print("Processing %s..." % fn)
        image = QImage(fn)
        num_tiles_x = image.width() // TILEWIDTH
        num_tiles_y = image.height() // TILEHEIGHT
        image_palette_data = {}
        for x in range(num_tiles_x):
            for y in range(num_tiles_y):
                rect = (x * TILEWIDTH, y * TILEHEIGHT, TILEWIDTH, TILEHEIGHT)
                palette = image.copy(*rect)
                d = QuadPaletteData(palette)
                image_palette_data[(x, y)] = d
        
        best_matches = {} # Position: Mountain Template match
        for position, palette in image_palette_data.items():
            mountain_match = is_present(palette, palette_templates)
            if mountain_match:
                best_matches[position] = mountain_match
        # print({k: v.coord for k, v in best_matches.items()})

        for position, mountain_match in best_matches.items():
            # Find adjacent positions
            left = position[0] - 1, position[1]
            right = position[0] + 1, position[1]
            up = position[0], position[1] - 1
            down = position[0], position[1] + 1
            left_palette = best_matches.get(left)
            right_palette = best_matches.get(right)
            up_palette = best_matches.get(up)
            down_palette = best_matches.get(down)
            # determine if those positions are in palette_templates
            # If they are, mark those coordinates in the list of valid coords
            # If not, mark as end validity
            if left[0] >= 0:
                if left_palette:
                    mountain_match.rules['left'][left_palette.coord] += 1
                else:
                    mountain_match.rules['left'][None] += 1
                    if mountain_match.coord in ((11, 16), (11, 18), (13, 16)):
                        print(fn, position, 'left', mountain_match.coord)
            if right[0] < num_tiles_x:
                if right_palette:
                    mountain_match.rules['right'][right_palette.coord] += 1
                else:
                    mountain_match.rules['right'][None] += 1
                    if mountain_match.coord in ((11, 23), (12, 15)):
                        print(fn, position, 'right', mountain_match.coord)
            if up[1] >= 0:
                if up_palette:
                    mountain_match.rules['up'][up_palette.coord] += 1
                else:
                    mountain_match.rules['up'][None] += 1
                    # if mountain_match.coord in ((2, 12), (1, 16), (1, 17), (4, 18), (8, 19), (9, 19)):
                    #     print(fn, position, 'up', mountain_match.coord)
            if down[1] < num_tiles_y:
                if down_palette:
                    mountain_match.rules['down'][down_palette.coord] += 1
                else:
                    mountain_match.rules['down'][None] += 1
                    if mountain_match.coord in ((13, 16), (17, 15)):
                        print(fn, position, 'down', mountain_match.coord)

def is_present(palette: QuadPaletteData, palette_templates: dict) -> MountainQuadPaletteData:
    MUST_MATCH = 4
    for coord, mountain in palette_templates.items():
        if similar(palette, mountain, MUST_MATCH):
            return mountain
    return None

def remove_useless_palettes(mountain_palettes: dict):
    # Remove useless palettes
    useless_limit = 8
    for coord in list(mountain_palettes.keys()):
        palette = mountain_palettes[coord]
        # Only bother with the ones that actually have rules
        if sum(palette.rules['left'].values()) >= useless_limit or \
                sum(palette.rules['right'].values()) >= useless_limit or \
                sum(palette.rules['up'].values()) >= useless_limit or \
                sum(palette.rules['down'].values()) >= useless_limit:
            pass
        else:
            del mountain_palettes[coord]
    # Now delete connections
    remaining_coords = mountain_palettes.keys()
    for palette in mountain_palettes.values():
        for direction in DIRECTIONS:
            palette.rules[direction] = {k: v for k, v in palette.rules[direction].items() if k in remaining_coords or k is None}
    return mountain_palettes

def remove_adjacent_palettes(mountain_palettes: dict):
    # Make it so that no coord can connect to itself
    for coord, palette in mountain_palettes.items():
        for direction in DIRECTIONS:
            palette.rules[direction] = {k: v for k, v in palette.rules[direction].items() if k != coord}
    return mountain_palettes

if __name__ == '__main__':
    import os, sys, glob
    try:
        import cPickle as pickle
    except ImportError:
        import pickle

    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)

    tileset = 'app/map_maker/palettes/westmarch/main.png'
    mountain_coords = get_mountain_coords(tileset)

    mountain_palettes = load_mountain_palettes(tileset, mountain_coords)
    home_dir = os.path.expanduser('~')
    mountain_data_dir = glob.glob(home_dir + '/Pictures/Fire Emblem/MapReferences/custom_mountain_data/*.png')
    # Stores rules in the palette data itself
    assign_rules(mountain_palettes, mountain_data_dir)
    mountain_palettes = remove_adjacent_palettes(mountain_palettes)
    mountain_palettes = remove_useless_palettes(mountain_palettes)

    print("--- Final Rules ---")
    final_rules = {coord: mountain_palette.rules for coord, mountain_palette in mountain_palettes.items()}
    # to_watch = []
    # for coord, rules in sorted(final_rules.items()):
    #     print("---", coord, "---")
    #     if rules['left']:
    #         print('left', rules['left'])
    #     if rules['right']:
    #         print('right', rules['right'])
    #     if rules['up']:
    #         print('up', rules['up'])
    #     if rules['down']:
    #         print('down', rules['down'])
    #     if None in rules['left'] and rules['left'][None] < (0.1 * sum(rules['left'].values())):
    #         to_watch.append((coord, 'left'))
    #     if None in rules['right'] and rules['right'][None] < (0.1 * sum(rules['right'].values())):
    #         to_watch.append((coord, 'right'))
    #     if None in rules['up'] and rules['up'][None] < (0.1 * sum(rules['up'].values())):
    #         to_watch.append((coord, 'up'))
    #     if None in rules['down'] and rules['down'][None] < (0.1 * sum(rules['down'].values())):
    #         to_watch.append((coord, 'down'))
    # print("--- Watch for: ---")
    # print(to_watch)

    data_loc = 'app/map_maker/mountain_data.p'
    with open(data_loc, 'wb') as fp:
        pickle.dump(final_rules, fp)
