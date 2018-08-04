from pprint import pprint
from Redy.Tools.PathLib import Path

import rbnf.zero as ze
import pytest
import unittest


class TestComments(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def test_ze(self):
        zero_exp = ze.compile(
            """
            # test
            import poly.[*] # 1234""",
            use='Poly')

        expected = [(0, 7), (1, 3), (2, 7), (5, -7), (11, 7)]

        self.assertEqual(
            zero_exp.match(
                "2x^2 + 3 + 4 - 7 x^5 + 4 x + 5 x ^2 - x + 7 x ^ 11").result,
            expected)
