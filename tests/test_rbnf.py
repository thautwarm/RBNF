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
from rbnf.core.State import State
from rbnf.bootstrap.rbnf import Grammar, rbnf, Language, _build_language

mylang = Language("mylang")
_build_language(codes, mylang, filename=__file__)

#
mylang.build()
#

from rbnf.core.State import State

tokens = list(mylang.lexer("a b c 10 8"))

state = State(mylang.implementation)
print(mylang.implementation['Z'])
print(mylang.named_parsers['Z'].match(tokens, state))
print(mylang.lang_name)
with open('test_compiled_rbnf.py', 'w') as f:
    f.write(mylang.dumps())
