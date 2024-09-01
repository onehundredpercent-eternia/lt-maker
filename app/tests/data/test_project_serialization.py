import json
import logging
import unittest
from pathlib import Path

class WholeProjectDeserializationTest(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def load_load_db_and_save_produces_same_result(self):
        from app.data.database.database import DB
        DB.load('testing_proj.ltproj')
        pass