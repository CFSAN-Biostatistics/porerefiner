# from unittest import TestCase, skip

from tests import paths

from porerefiner import notifiers


def test_number_of_classes(self):
    assert len(notifiers.REGISTRY) >= 3
