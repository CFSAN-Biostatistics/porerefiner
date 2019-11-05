from unittest import TestCase, skip

from tests import paths, with_database, TestBase

from porerefiner import notifiers

class TestNotifierBaseClass(TestCase):

    def test_number_of_classes(self):
        self.assertGreaterEqual(len(notifiers.REGISTRY), 3)
