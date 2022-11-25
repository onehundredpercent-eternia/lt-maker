from app.data.database.database import DB
from app.engine.game_state import game
from app.utilities import static_random
import logging

def completed_chapters() -> int:
    return game.game_vars.get('completed_chapters', 0)

def get_random_item(tags=None, exclude=None, pos=(0, 0)) -> str:
    tags = tags or []
    exclude = exclude or []
    logging.debug("Get random item with tags %s and exclude %s", tags, exclude)
    all_items = []
    all_chances = []
    for tag in tags:
        if tag == 'Forge':
            chance = 10
            items = [item for item in DB.items if item.item_tags and tag in item.item_tags.value]
        elif tag == 'Promo':
            chance = 10
            items = [item for item in DB.items if item.item_tags and tag in item.item_tags.value]
        else:
            chance = 30
            items = [item for item in DB.items if item.item_tags and tag in item.item_tags.value]
        items = [item for item in items if item.nid not in exclude]
        assert len(items) >= 1
        all_items.append(items)
        all_chances.append(chance)
    assert len(all_items) >= 1
    assert len(all_chances) >= 1
    logging.debug(all_items)
    logging.debug(all_chances)
    generator: static_random.LCG = \
        static_random.get_generator_from_pos(pos, completed_chapters())
    idx = static_random.weighted_choice(all_chances, generator)
    items = all_items[idx]
    assert len(items) >= 1
    logging.debug(items)
    item = generator.choice(items)
    logging.debug(item.nid)
    return item.nid

def get_random_tree_item(pos: tuple = (0, 0)):
    chapter_num = completed_chapters()
    if chapter_num == 0:
        tags = ['Weapon']
    elif chapter_num == 1:
        tags = ['Weapon', 'Spell', 'Accessory']
    elif chapter_num == 2:
        tags = ['Weapon', 'Spell', 'Forge', 'Accessory']
    elif chapter_num == 3:
        tags = ['Weapon', 'Spell', 'Forge', 'Accessory']
    elif chapter_num == 4:
        tags = ['Weapon', 'Spell', 'Forge', 'Promo', 'Accessory']
    elif chapter_num == 5:
        tags = ['Weapon', 'Weapon+', 'Spell', 'Forge', 'Promo', 'Accessory', 'Accessory+']
    elif chapter_num == 6:
        tags = ['Weapon+', 'Spell', 'Spell+', 'Forge', 'Promo', 'Accessory', 'Accessory+']
    elif chapter_num == 7:
        tags = ['Weapon+', 'Spell+', 'Promo', 'Accessory+']
    elif chapter_num >= 8:
        tags = ['Weapon+', 'Spell+', 'Accessory+']
    return get_random_item(tags, pos=pos)
