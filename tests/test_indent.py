import unittest
import rbnf.zero as ze
import pytest


class TestDocTransformation(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def test_doctrans(self):
        ze_exp = ze.compile("""
        pyimport rbnf.std.common.[recover_codes]
        LexerHelper := R'.'
        Formula ::= '`' (~'`')+ as content '`'
                rewrite " :math:`"+recover_codes(content)+'` '
        Unit ::= Formula as formula | _ as other
                 rewrite
                    formula if not other else other.value
        Text ::= Unit+ as seq
                 rewrite ''.join(seq)
        """)

        self.assertEqual(
            ze_exp.match('abcdefg `\lambda + 1` + 1').result,
            'abcdefg  :math:`\lambda + 1`  + 1')
        ze_exp.lang.as_fixed()
        self.assertEqual(
            ze_exp.match('abcdefg `\lambda + 1` + 1').result,
            'abcdefg  :math:`\lambda + 1`  + 1')


if __name__ == '__main__':
    unittest.main()
