# Takes a tilemap and converts to Dungeon Maker images
import os
import json
from PIL import Image

# === Change These ===
palette_type = 'castle'  # What kind of tilemap is this
fn = '../palettes/0A00DC0C-mystic.png'  # The base tilemap to grab the tile from
palette_name = '../palettes/mystic'  # The folder to put this into
# === End Change These ===

if not os.path.exists(palette_name):
    os.mkdir(palette_name)

# Floor types: default, grass, ruins, checkerboard

d = {'floor1': "default",
     'floor2': "checkerboard",
     'water': True}

with open(os.path.join(palette_name, 'metadata.json'), 'w') as fp:
    json.dump(d, fp, indent=4)

base_tiles = Image.open(fn)

# Floor1
tiles = [(144, 416), (160, 416)]
floor1 = Image.new('RGBA', (16, 16 * len(tiles)))
for idx, tile in enumerate(tiles):
    i = base_tiles.crop((tile[0], tile[1], tile[0] + 16, tile[1] + 16))
    floor1.paste(i, (0, 16 * idx))
floor1.save(os.path.join(palette_name, 'floor1.png'))

# Floor1Shading
left = base_tiles.crop((192, 432, 192 + 8, 432 + 16))
top = base_tiles.crop((176, 416, 176 + 16, 416 + 2))
corner = base_tiles.crop((192, 400, 192 + 8, 400 + 8))
lefttop = base_tiles.crop((192, 432, 192 + 16, 432 + 16))
cornertop = base_tiles.crop((192, 432, 192 + 16, 432 + 8))
pillar_bottom = base_tiles.crop((208, 400, 208 + 16, 400 + 8))
shaded_pillar_bottom = base_tiles.crop((208, 400, 208 + 16, 400 + 8))
column_bottom = base_tiles.crop((112, 432, 112 + 16, 432 + 8))
floor1_shading = Image.new('RGBA', (8 * 16, 16))
floor1_shading.paste(left, (0, 0))
floor1_shading.paste(top, (16, 0))
floor1_shading.paste(corner, (32, 0))
floor1_shading.paste(lefttop, (48, 0))
floor1_shading.paste(cornertop, (64, 0))
floor1_shading.paste(pillar_bottom, (80, 0))
floor1_shading.paste(shaded_pillar_bottom, (96, 0))
floor1_shading.paste(column_bottom, (112, 0))
floor1_shading.save(os.path.join(palette_name, 'floor1_shading.png'))

# Floor2_alpha
tiles = [(272, 352),]
floor2_alpha = Image.new('RGBA', (16, 16 * len(tiles)))
for idx, tile in enumerate(tiles):
    i = base_tiles.crop((tile[0], tile[1], tile[0] + 16, tile[1] + 16))
    floor2_alpha.paste(i, (0, 16 * idx))
floor2_alpha.save(os.path.join(palette_name, 'floor2.png'))

# Floor2Shading_alpha
left = base_tiles.crop((256, 352, 256 + 8, 352 + 16))
top = base_tiles.crop((288, 352, 288 + 16, 352 + 4))
corner = base_tiles.crop((304, 368, 304 + 8, 368 + 8))
lefttop = base_tiles.crop((304, 352, 304 + 16, 352 + 16))
cornertop = base_tiles.crop((304, 352, 304 + 16, 352 + 8))
pillar_bottom = base_tiles.crop((240, 368, 240 + 16, 368 + 8))
shaded_pillar_bottom = base_tiles.crop((224, 432, 224 + 16, 432 + 8))
column_bottom = base_tiles.crop((48, 272, 48 + 16, 272 + 8))
floor2_shading_alpha = Image.new('RGBA', (8 * 16, 16))
floor2_shading_alpha.paste(left, (0, 0))
floor2_shading_alpha.paste(top, (16, 0))
floor2_shading_alpha.paste(corner, (32, 0))
floor2_shading_alpha.paste(lefttop, (48, 0))
floor2_shading_alpha.paste(cornertop, (64, 0))
floor2_shading_alpha.paste(pillar_bottom, (80, 0))
floor2_shading_alpha.paste(shaded_pillar_bottom, (96, 0))
floor2_shading_alpha.paste(column_bottom, (112, 0))
floor2_shading_alpha.save(os.path.join(palette_name, 'floor2_shading.png'))

# Floor2_beta
tiles = [(272, 384),]
floor2_beta = Image.new('RGBA', (16, 16 * len(tiles)))
for idx, tile in enumerate(tiles):
    i = base_tiles.crop((tile[0], tile[1], tile[0] + 16, tile[1] + 16))
    floor2_beta.paste(i, (0, 16 * idx))
floor2_beta.save(os.path.join(palette_name, 'floor2_beta.png'))

# Floor2Shading_beta
left = base_tiles.crop((256, 384, 256 + 8, 384 + 16))
top = base_tiles.crop((288, 384, 288 + 16, 384 + 4))
corner = base_tiles.crop((288, 368, 288 + 8, 368 + 8))
lefttop = base_tiles.crop((304, 384, 304 + 16, 384 + 16))
cornertop = base_tiles.crop((304, 384, 304 + 16, 384 + 8))
pillar_bottom = base_tiles.crop((240, 384, 240 + 16, 384 + 8))
shaded_pillar_bottom = base_tiles.crop((208, 416, 208 + 16, 416 + 8))
column_bottom = base_tiles.crop((64, 272, 64 + 16, 272 + 8))
floor2_shading_beta = Image.new('RGBA', (8 * 16, 16))
floor2_shading_beta.paste(left, (0, 0))
floor2_shading_beta.paste(top, (16, 0))
floor2_shading_beta.paste(corner, (32, 0))
floor2_shading_beta.paste(lefttop, (48, 0))
floor2_shading_beta.paste(cornertop, (64, 0))
floor2_shading_beta.paste(pillar_bottom, (80, 0))
floor2_shading_beta.paste(shaded_pillar_bottom, (96, 0))
floor2_shading_beta.paste(column_bottom, (112, 0))
floor2_shading_beta.save(os.path.join(palette_name, 'floor2_shading_beta.png'))

# Forest & Pillar
tiles = [(240, 352),]
pillar = Image.new('RGBA', (16, 16 * len(tiles)))
for idx, tile in enumerate(tiles):
    i = base_tiles.crop((tile[0], tile[1], tile[0] + 16, tile[1] + 16))
    pillar.paste(i, (0, 16 * idx))
pillar.save(os.path.join(palette_name, 'forest.png'))
pillar.save(os.path.join(palette_name, 'pillar.png'))

# StairsLeft
stairs = Image.new('RGBA', (16 * 4, 16))
stairs.paste(base_tiles.crop((112, 208, 112 + 16, 208 + 16)), (0, 0))
stairs.paste(base_tiles.crop((96, 208, 96 + 16, 208 + 16)), (16, 0))
stairs.paste(base_tiles.crop((48, 192, 48 + 16, 192 + 16)), (32, 0))
stairs.paste(base_tiles.crop((16, 192, 16 + 16, 192 + 16)), (48, 0))
stairs.save(os.path.join(palette_name, 'stairs_left.png'))

# StairsRight
stairs = Image.new('RGBA', (16 * 4, 16))
stairs.paste(base_tiles.crop((80, 208, 80 + 16, 208 + 16)), (0, 0))
stairs.paste(base_tiles.crop((96, 208, 96 + 16, 208 + 16)), (16, 0))
stairs.paste(base_tiles.crop((32, 192, 32 + 16, 192 + 16)), (32, 0))
stairs.paste(base_tiles.crop((16, 192, 16 + 16, 192 + 16)), (48, 0))
stairs.save(os.path.join(palette_name, 'stairs_right.png'))

# Stairs
stairs = Image.new('RGBA', (16 * 4, 16))
stairs.paste(base_tiles.crop((64, 208, 64 + 16, 208 + 16)), (0, 0))
stairs.paste(base_tiles.crop((64, 224, 64 + 16, 224 + 16)), (16, 0))
stairs.paste(base_tiles.crop((80, 224, 80 + 16, 224 + 16)), (32, 0))
stairs.paste(base_tiles.crop((96, 224, 96 + 16, 224 + 16)), (48, 0))
stairs.save(os.path.join(palette_name, 'stairs_updown.png'))

# StartEnd
stairs = Image.new('RGBA', (16 * 2, 16))
stairs.paste(base_tiles.crop((48, 208, 48 + 16, 208 + 16)), (0, 0))
stairs.paste(base_tiles.crop((48, 208, 48 + 16, 208 + 16)), (16, 0))
stairs.save(os.path.join(palette_name, 'start_end.png'))

# Void
void = Image.new('RGBA', (16, 16))
void.paste(base_tiles.crop((48, 176, 48 + 16, 176 + 16)), (0, 0))
void.save(os.path.join(palette_name, 'void.png'))

# Wall Bottom
alone = [(144, 384)]
left = [(192, 384)]
right = [(208, 384)]
both = [(160, 384)]
shadow = [(224, 400)]
shadow_alone = [(224, 384)]
column = [(112, 416)]
longest_list = max(len(tiles) for tiles in [alone, left, right, both, shadow, shadow_alone, column])
wall = Image.new('RGBA', (16 * 7, 16 * longest_list + 16))
for idx, tile in enumerate(alone):
    wall.paste(base_tiles.crop((tile[0], tile[1], tile[0] + 16, tile[1] + 16)), (0, 16 * idx))
for idx, tile in enumerate(left):
    wall.paste(base_tiles.crop((tile[0], tile[1], tile[0] + 16, tile[1] + 16)), (16, 16 * idx))
for idx, tile in enumerate(right):
    wall.paste(base_tiles.crop((tile[0], tile[1], tile[0] + 16, tile[1] + 16)), (32, 16 * idx))
for idx, tile in enumerate(both):
    wall.paste(base_tiles.crop((tile[0], tile[1], tile[0] + 16, tile[1] + 16)), (48, 16 * idx))
for idx, tile in enumerate(shadow):
    wall.paste(base_tiles.crop((tile[0], tile[1], tile[0] + 16, tile[1] + 16)), (64, 16 * idx))
for idx, tile in enumerate(shadow_alone):
    wall.paste(base_tiles.crop((tile[0], tile[1], tile[0] + 16, tile[1] + 16)), (80, 16 * idx))
for idx, tile in enumerate(column):
    wall.paste(base_tiles.crop((tile[0], tile[1], tile[0] + 16, tile[1] + 16)), (96, 16 * idx))
wall.save(os.path.join(palette_name, 'wall_bottom.png'))

# Wall Top
column = [(64, 240)]
north = [(160, 240)]
east = [(192, 240), (128, 272)]
ne = [(192, 240), (128, 272)]
south = [(160, 224)]
ns = [(176, 224), (176, 240)]
se = [(208, 256)]
sen = [(208, 256)]
west = [(224, 256), (144, 272)]
nw = [(224, 256), (144, 272)]
ew = [(192, 224), (224, 224)]
new = [(192, 224), (224, 224)]
sw = [(208, 240)]
nsw = [(208, 240)]
wse = [(208, 224)]
nesw = [(208, 224)]

chunk = (128, 208)
east_chunk = (128, 240)
west_chunk = (144, 240)
left_chunk = (96, 272)
right_chunk = (112, 272)

wall_top = Image.new('RGBA', (256, 96))
for idx, tile in enumerate(column):
    wall_top.paste(base_tiles.crop((tile[0], tile[1], tile[0] + 16, tile[1] + 16)), (0, 16 * idx))
for idx, tile in enumerate(north):
    wall_top.paste(base_tiles.crop((tile[0], tile[1], tile[0] + 16, tile[1] + 16)), (16, 16 * idx))
for idx, tile in enumerate(east):
    wall_top.paste(base_tiles.crop((tile[0], tile[1], tile[0] + 16, tile[1] + 16)), (32, 16 * idx))
for idx, tile in enumerate(ne):
    wall_top.paste(base_tiles.crop((tile[0], tile[1], tile[0] + 16, tile[1] + 16)), (48, 16 * idx))
for idx, tile in enumerate(south):
    wall_top.paste(base_tiles.crop((tile[0], tile[1], tile[0] + 16, tile[1] + 16)), (64, 16 * idx))
for idx, tile in enumerate(ns):
    wall_top.paste(base_tiles.crop((tile[0], tile[1], tile[0] + 16, tile[1] + 16)), (80, 16 * idx))
for idx, tile in enumerate(se):
    wall_top.paste(base_tiles.crop((tile[0], tile[1], tile[0] + 16, tile[1] + 16)), (96, 16 * idx))
for idx, tile in enumerate(sen):
    wall_top.paste(base_tiles.crop((tile[0], tile[1], tile[0] + 16, tile[1] + 16)), (112, 16 * idx))
for idx, tile in enumerate(west):
    wall_top.paste(base_tiles.crop((tile[0], tile[1], tile[0] + 16, tile[1] + 16)), (128, 16 * idx))
for idx, tile in enumerate(nw):
    wall_top.paste(base_tiles.crop((tile[0], tile[1], tile[0] + 16, tile[1] + 16)), (144, 16 * idx))
for idx, tile in enumerate(ew):
    wall_top.paste(base_tiles.crop((tile[0], tile[1], tile[0] + 16, tile[1] + 16)), (160, 16 * idx))
for idx, tile in enumerate(new):
    wall_top.paste(base_tiles.crop((tile[0], tile[1], tile[0] + 16, tile[1] + 16)), (176, 16 * idx))
for idx, tile in enumerate(sw):
    wall_top.paste(base_tiles.crop((tile[0], tile[1], tile[0] + 16, tile[1] + 16)), (192, 16 * idx))
for idx, tile in enumerate(nsw):
    wall_top.paste(base_tiles.crop((tile[0], tile[1], tile[0] + 16, tile[1] + 16)), (208, 16 * idx))
for idx, tile in enumerate(wse):
    wall_top.paste(base_tiles.crop((tile[0], tile[1], tile[0] + 16, tile[1] + 16)), (224, 16 * idx))
for idx, tile in enumerate(nesw):
    wall_top.paste(base_tiles.crop((tile[0], tile[1], tile[0] + 16, tile[1] + 16)), (240, 16 * idx))
# Chunks
wall_top.paste(base_tiles.crop((chunk[0], chunk[1], chunk[0] + 16, chunk[1] + 16)), (240, 48))
wall_top.paste(base_tiles.crop((east_chunk[0], east_chunk[1], east_chunk[0] + 16, east_chunk[1] + 16)), (240, 64))
wall_top.paste(base_tiles.crop((west_chunk[0], west_chunk[1], west_chunk[0] + 16, west_chunk[1] + 16)), (240, 80))
wall_top.paste(base_tiles.crop((left_chunk[0], left_chunk[1], left_chunk[0] + 16, left_chunk[1] + 16)), (224, 64))
wall_top.paste(base_tiles.crop((right_chunk[0], right_chunk[1], right_chunk[0] + 16, right_chunk[1] + 16)), (224, 80))
wall_top.save(os.path.join(palette_name, 'wall_top.png'))

# Water
open_water_tiles = [(336, 96)]
closed_water_tiles = [(320, 96), (320, 128), (320, 112), (336, 112), (336, 128),]
water = Image.new('RGBA', (16 * 2, 16 * len(closed_water_tiles)))
for idx, tile in enumerate(open_water_tiles):
    water.paste(base_tiles.crop((tile[0], tile[1], tile[0] + 16, tile[1] + 16)), (0, 16 * idx))
for idx, tile in enumerate(closed_water_tiles):
    water.paste(base_tiles.crop((tile[0], tile[1], tile[0] + 16, tile[1] + 16)), (16, 16 * idx))
water.save(os.path.join(palette_name, 'water.png'))

# Water Shading
water_shading = Image.new('RGBA', (16 * 5, 16))
# Left
water_shading.paste(base_tiles.crop((368, 80, 368 + 8, 80 + 16)), (0, 0))
# Top
water_shading.paste(base_tiles.crop((352, 80, 352 + 16, 80 + 8)), (16, 0))
# Left Top
water_shading.paste(base_tiles.crop((368, 96, 368 + 16, 96 + 16)), (32, 0))
# Column
water_shading.paste(base_tiles.crop((400, 256, 400 + 16, 256 + 16)), (48, 0))
# Column Left
water_shading.paste(base_tiles.crop((400, 256, 400 + 16, 256 + 16)), (64, 0))
water_shading.save(os.path.join(palette_name, 'water_shading.png'))

# Bridge
tiles = [(304, 208), (304, 224), (320, 224)]
shading = [(336, 208)]
bridge = Image.new('RGBA', (16 * 2, len(tiles) * 16))
for idx, tile in enumerate(tiles):
    bridge.paste(base_tiles.crop((tile[0], tile[1], tile[0] + 16, tile[1] + 16)), (0, idx * 16))
for idx, tile in enumerate(shading):
    bridge.paste(base_tiles.crop((tile[0], tile[1], tile[0] + 4, tile[1] + 16)), (16, idx))
bridge.save(os.path.join(palette_name, 'bridge.png'))
