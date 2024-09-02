import unittest

from app.utilities.data import Data

class DataObjectTests(unittest.TestCase):
    """
    Tests the Data object
    """
    def test_copy_data_simple(self):
        data = Data()
        data.append(2)

        copy = data.copy()

        self.assertEqual(len(copy), 1)
        self.assertEqual(copy, 2)
