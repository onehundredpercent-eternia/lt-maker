import unittest
from unittest.mock import MagicMock, patch, call
from app.data.database.database_types import DatabaseType
from app.data.database_validator import DatabaseValidatorEngine

from app.data.database.database import Database
from app.data.resources.resources import Resources

class DBValidatorTests(unittest.TestCase):
    def setUp(self):
        self.db = Database()
        self.resources = Resources()
        self.db.load('testing_proj.ltproj')
        self.resources.load('testing_proj.ltproj')
        self.db_validator = DatabaseValidatorEngine(self.db, self.resources)

    def tearDown(self) -> None:
        pass

    def test_all_types_have_validators(self):
        for db_type in DatabaseType:
            self.assertTrue(db_type in self.db_validator._validate_db)


if __name__ == '__main__':
    unittest.main()
