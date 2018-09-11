from rbnf.core.Tokenizer import Tokenizer
from rbnf.easy import ze
from rbnf.core.AST import Named


def test_lr(fixed=False):
    ze_exp = ze.compile(
        """
A ::= (B D) as bd | 'a' as a
      rewrite bd if bd else a.value
B ::= A as a 'b' as b
      rewrite (a, b.value)    
D ::= D as d 'd' as lit | 'e' as e
      rewrite e.value if e else (d, lit.value) 
    """,
        use='A')
    assert ze_exp.match('abebedbe').result == [([([('a', 'b'), 'e'], 'b'),
                                                 ('e', 'd')], 'b'), 'e']
