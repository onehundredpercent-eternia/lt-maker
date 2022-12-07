self.scratch_data: dict = None   # Contains data to recreate this tilemapobject from scratch

@classmethod
def build_from_scratch(cls, nid, dungeon, surf, scratch_data):
    self = cls()
    self.nid = nid
    self.width = dungeon.width
    self.height = dungeon.height
    self.autotile_fps = 0
    self.layers = Data()
    self.scratch_data = scratch_data

    # Build a layer
    base_layer = LayerObject('base', self)
    
    for coord, terrain_nid in dungeon.get_true_terrain_grid().items():
        base_layer.terrain[coord] = terrain_nid

    image = engine.create_surface((self.width * TILEWIDTH, self.height * TILEHEIGHT))
    engine.fill(image, COLORKEY)
    engine.set_colorkey(image, COLORKEY, rleaccel=True)
    image.blit(surf, (0, 0))

    right_bound = (max(coord[0] for coord in dungeon.terrain_grid) + 1) * TILEWIDTH
    bottom_bound = (max(coord[1] for coord in dungeon.terrain_grid) + 1) * TILEHEIGHT
    base_layer.pixel_bounds = [0, 0, right_bound, bottom_bound]

    base_layer.image = image
    base_layer.visible = True

    self.layers.append(base_layer)

    return self

    @classmethod
    def restore(cls, s_dict):
        if s_dict.get('scratch_data'):
            from app.dungeon_maker import map_generator
            self = map_generator.build_tilemap(**s_dict['scratch_data'])
        else:
            prefab = RESOURCES.tilemaps.get(s_dict['nid'])
            self = cls.from_prefab(prefab)
        self.restore_layers(s_dict['layers'])
    ...