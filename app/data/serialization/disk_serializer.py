import logging
import os
from pathlib import Path
import re
import shutil
from typing import List
from app.data.database import database
from app.data.resources import resources
from app.utilities.serialization import save_json
from app.utilities.typing import NestedPrimitiveDict

class Serializer():
    @staticmethod
    def save_database(game_dir: Path, database_as_dict: NestedPrimitiveDict, as_chunks: bool):
        # This section is what takes so long!
        data_dir = game_dir / 'game_data'
        try:
            for key, value in database_as_dict.items():
                # divide save data into chunks based on key value
                if key in database.Database.save_as_chunks and as_chunks:
                    save_dir = data_dir / key
                    if save_dir.exists():
                        shutil.rmtree(save_dir)
                    os.mkdir(save_dir)
                    orderkeys: List[str] = []
                    for idx, subvalue in enumerate(value):
                        # ordering
                        name = subvalue['nid']
                        name = re.sub(r'[\\/*?:"<>|]', "", name)
                        name = name.replace(' ', '_')
                        orderkeys.append(name)
                        save_loc = Path(save_dir, name + '.json')
                        # logging.info("Serializing %s to %s" % ('%s/%s.json' % (key, name), save_loc))
                        save_json(save_loc, [subvalue])
                    save_json(Path(save_dir, '.orderkeys'), orderkeys)
                else:  # Save as a single file
                    # Which means deleting the old directory
                    save_dir = Path(data_dir, key)
                    if os.path.exists(save_dir):
                        shutil.rmtree(save_dir)
                    save_loc = Path(data_dir, key + '.json')
                    # logging.info("Serializing %s to %s" % (key, save_loc))
                    save_json(save_loc, value)

        except OSError as e:  # In case we ran out of memory
            logging.error("Editor was unable to save your project. Free up memory in your hard drive or try saving somewhere else, otherwise progress will be lost when the editor is closed.")
            logging.exception(e)
            return False

    @staticmethod
    def save_resources(game_dir: Path, resources_as_dict: NestedPrimitiveDict, as_chunks: bool):
            resource_dir = game_dir / 'resources'
            # serialize manifest data
            try:
                for key, value in resources_as_dict.items():
                    save_dir = Path(resource_dir, key)
                    # if chunks, delete the old directory
                    actual_save_dir = save_dir
                    if key in resources.Resources.save_as_chunks:
                        if key == 'tilemaps':
                            actual_save_dir = Path(save_dir, 'tilemap_data')
                        elif key == 'combat_palettes':
                            actual_save_dir = Path(save_dir, 'palette_data')
                        if os.path.exists(actual_save_dir):
                            shutil.rmtree(actual_save_dir)
                    # divide save data into chunks based on key value
                    if not os.path.exists(actual_save_dir):
                        os.makedirs(actual_save_dir)
                    if key in resources.Resources.save_as_chunks and as_chunks:
                        orderkeys: List[str] = []
                        for idx, subvalue in enumerate(value):
                            # ordering
                            if key == 'combat_palettes':
                                name = subvalue[0]
                            else:
                                name = subvalue['nid']
                            name = re.sub(r'[\\/*?:"<>|]', "", name)
                            name = name.replace(' ', '_')
                            orderkeys.append(name)
                            save_loc = Path(actual_save_dir, name + '.json')
                            # logging.info("Serializing %s to %s" % ('%s/%s.json' % (key, name), save_loc))
                            save_json(save_loc, [subvalue])
                        save_json(Path(actual_save_dir, '.orderkeys'), orderkeys)
                    else:  # Save as a single file
                        save_loc = Path(actual_save_dir, key + '.json')
                        # logging.info("Serializing %s to %s" % (key, save_loc))
                        save_json(save_loc, value)
            except OSError as e:  # In case we ran out of memory
                logging.error("Editor was unable to save your project. Free up memory in your hard drive or try saving somewhere else, otherwise progress will be lost when the editor is closed.")
                logging.exception(e)
                return False
