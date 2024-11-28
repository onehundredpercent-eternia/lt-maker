
from app.data.serialization.migrators.migrator_base import MigratorBase

class Migrator01(MigratorBase):
    def migrate_database(self, db_dict):
        return db_dict

    def migrate_resources(self, resource_dict):
        music_as_dict = []
        for music_tuple in resource_dict.get('music', []):
            if len(music_tuple) == 3:
                nid, has_intro, has_battle = music_tuple
                music_as_dict.append({'nid': nid, 'format': 'ogg'})
        resource_dict['music'] = music_as_dict
        return resource_dict