from app.data.database.database import DB
from app.engine.game_state import game
from app.utilities import static_random
import logging

def completed_chapters() -> int:
    return game.game_vars.get('completed_chapters', 0)

def get_random_item(tags: list = None, exclude: list = None, pos=(0, 0)) -> str:
    tags = tags or []
    exclude = exclude or []
    logging.debug("Get random item with tags %s and exclude %s", tags, exclude)
    all_items = []
    all_chances = []
    for tag in tags:
        if tag == 'Promo':
            chance = 20
        elif tag in ('Accessory', 'Accessory+'):
            chance = 45
        else:
            chance = 30
        items = [item for item in DB.items if item.item_tags and tag in item.item_tags.value]
        if tag in ('Weapon', 'Weapon+', 'Spell', 'Spell+'):
            # Don't allow two of the same weapon type in the three item choice
            items = [item for item in items if item.item_tags.value not in exclude]
        items = [item for item in items if item.nid not in exclude]
        assert len(items) >= 1
        all_items.append(items)
        all_chances.append(chance)
    assert len(all_items) >= 1
    assert len(all_chances) >= 1
    logging.debug(all_chances)
    generator: static_random.LCG = \
        static_random.get_generator_from_pos(pos, completed_chapters())
    logging.debug(pos)
    logging.debug(generator.state)
    idx = static_random.weighted_choice(all_chances, generator)
    items = all_items[idx]
    assert len(items) >= 1
    logging.debug([i.nid for i in items])
    item = generator.choice(items)
    logging.debug(item.nid)
    return item.nid

def get_random_tree_item(pos: tuple = (0, 0)):
    chapter_num = completed_chapters()
    if chapter_num == 0:
        tags = ['Weapon']
    elif chapter_num in (1, 2, 3):
        tags = ['Weapon', 'Spell', 'Accessory']
    elif chapter_num == 4:
        tags = ['Weapon', 'Spell', 'Promo', 'Accessory']
    elif chapter_num == 5:
        tags = ['Weapon', 'Weapon+', 'Spell', 'Promo', 'Accessory', 'Accessory+']
    elif chapter_num == 6:
        tags = ['Weapon+', 'Spell', 'Spell+', 'Promo', 'Accessory', 'Accessory+']
    elif chapter_num == 7:
        tags = ['Weapon+', 'Spell+', 'Promo', 'Accessory+']
    elif chapter_num >= 8:
        tags = ['Weapon+', 'Spell+', 'Accessory+']
    return get_random_item(tags, pos=pos)

def get_random_grave(tag: str, unit) -> str:
    logging.debug("Get random item with tag %s", tag)
    if 'Dancer' in unit.tags:
        return 'Refresh'
    # Only items that match the main tag
    items = [item for item in DB.items if item.item_tags and tag in item.item_tags.value]
    # Only items that match the tags of the unit (Sword for Sword units, Axe for Axe units, etc.)
    items = [item for item in items if any(t in item.item_tags.value for t in unit.tags)]
    logging.debug([item.nid for item in items])
    generator: static_random.LCG = \
        static_random.get_generator_from_unit(unit.nid)
    logging.debug(unit.nid)
    logging.debug(generator.state)
    assert len(items) > 0
    item = generator.choice(items)
    logging.debug(item.nid)
    return item.nid
