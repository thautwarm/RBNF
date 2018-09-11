import unittest
import pytest


class TestSimpleXML(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def test_simple_xml(self):
        import rbnf.zero as ze

        ze_exp = ze.compile("""
        import std.common.[Name Space] 
        # import `Name` and `Space` from $RBNF_HOME/std/common  
        
        XML ::= 
            | '<' t1=Name '/' '>'
            | '<' t1=Name '>' (XML | (seq << ~('<' '/' Name '>')))* '<' '/'  t2=Name '>'
            with
                't2' not in state.ctx or t1.value == t2.value
            rewrite
                t1.value, seq if seq else ()
        """)

        print(ze_exp.match('<a> b </a>').result)
