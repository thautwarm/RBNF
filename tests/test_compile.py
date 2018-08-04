import unittest
import pytest


class TestCompile(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def test_compile(self):

        codes = ("""
        ignore[Space]
        Space := R'\s'
        Name := R'[a-zA-Z]+'
        Num := R'\d+'
        Alpha cast := 'a' 'b' 'c'
        
        Z ::= Alpha+ Num as n1 Num as n2
                with
                    d1 = int(n1.value)
                    d2 = int(n2.value)
                    return d1 > d2
        """)

        from rbnf.bootstrap.rbnf import build_language, Language
        mylang = Language("mylang")
        build_language(codes, mylang, filename=__file__)
        mylang.dump('compiled_rbnf.py')
