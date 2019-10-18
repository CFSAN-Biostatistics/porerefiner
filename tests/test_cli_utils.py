

from hypothesis import given
import hypothesis.strategies as strat
from hypothesis_fspaths import fspaths

from unittest import TestCase

class TestUtilities(TestCase):

    @given(path=fspaths())
    def test_inverse_ops(self, path):
        from porerefiner.cli_utils import relativize_path, absolutize_path
        assert path == relativize_path(absolutize_path(path))
        assert path == absolutize_path(relativize_path(path))
