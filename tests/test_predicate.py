import rbnf.zero as ze
import sys, os
from rbnf.easy import build_parser
from Redy.Tools.PathLib import Path
pwd = Path(__file__).parent().__str__()
sys.path.append(pwd)
os.chdir(pwd)


def test_predicate():
    ze_exp = ze.compile(
        """
[python] import predicate_helpers.[*]
lexer_helper := R'.'
a ::= (_{is_ok})+
b ::= (_+){not_ok}
        """,
        use='a')

    assert len(ze_exp.match("123234").result.item) == 2

    ze_exp = ze.compile(
        """
[python] import predicate_helpers.[*]
lexer_helper := R'.'
a ::= (_{is_ok})+
b ::= (_+){not_ok}
        """,
        use='b')

    assert ze_exp.match("123234").result == None
    print(ze_exp.dumps())
