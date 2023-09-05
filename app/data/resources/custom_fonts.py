from app.data.resources.base_catalog import ManifestCatalog

class GameFont():
    def __init__(self, nid, full_path=None, pixmap=None):
        self.nid = nid
        self.full_path = full_path

    def set_full_path(self, full_path):
        self.full_path = full_path

    def save(self):
        s_dict = {}
        s_dict['nid'] = self.nid
        return s_dict

    @classmethod
    def restore(cls, s_dict):
        return cls(s_dict['nid'])

class GameFontCatalog(ManifestCatalog[GameFont]):
    manifest = 'fonts.json'
    title = 'fonts'
    datatype = GameFont
