import unittest



class UnitObjectUnitTests(unittest.TestCase):
    def setUp(self):
        from app.data.database import DB
        DB.load('default.ltproj')
        from app.engine.objects.unit import UnitObject
        self.db_unit = UnitObject.from_prefab(DB.units.get("Eirika"))                # eirika, prefab
        # self.level_unit = UnitObject.from_prefab(DB.levels[0].units.get("Eirika"))   # eirika, level unit
        # self.generic_unit = UnitObject.from_prefab(DB.levels[0].units.get("101"))    # warrior, generic level unit

    def test_db_unit_constructor(self):
        unit = self.db_unit
        from app.data.database import DB
        from app.data.units import UnitPrefab
        self.assertEqual(unit.nid, "Eirika")
        self.assertEqual(unit.generic, False)
        self.assertEqual(unit.persistent, True)
        self.assertEqual(unit.ai, None)
        self.assertEqual(unit.ai_group, None)
        self.assertEqual(unit.faction, None)
        self.assertEqual(unit.team, "player")
        self.assertEqual(unit.portrait_nid, "Eirika")
        self.assertEqual(unit.affinity, "Light")
        self.assertEqual(unit.notes, [])
        self.assertEqual(unit._fields, {})
        self.assertEqual(unit.klass, "Eirika_Lord")
        self.assertEqual(unit.variant, None)

        self.assertEqual(unit.name, "Eirika")
        self.assertEqual(unit.desc, "The princess of the Kingdom of\nRenais. She's elegant and kind.")
        self.assertEqual(unit.tags, ['Lord', 'Sword'])
        self.assertEqual(unit.party, None)
        self.assertEqual(unit.level, 1)
        self.assertEqual(unit.exp, 0)
        self.assertEqual(unit.stats, {
            "HP": 16,
            "STR": 4,
            "MAG": 2,
            "SKL": 8,
            "SPD": 9,
            "LCK": 5,
            "DEF": 3,
            "CON": 5,
            "MOV": 5,
            "RES": 1
        })
        self.assertEqual(unit.growths, {
             "HP": 70,
            "STR": 40,
            "MAG": 20,
            "SKL": 60,
            "SPD": 60,
            "LCK": 60,
            "DEF": 30,
            "CON": 0,
            "MOV": 0,
            "RES": 30
        })


if __name__ == '__main__':
    unittest.main()
