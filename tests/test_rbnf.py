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
from rbnf.State import State
from rbnf.bootstrap.rbnf import Grammar, rbnf, Language

state = State(rbnf.implementation)
state.data = Language("mylang")
state.filename = __file__
tokens = tuple(rbnf.lexer(codes))
Grammar.match(tokens, state)
ULexer = rbnf.implementation['ULexer'][0]

mylang = state.data
#
mylang.build()
#
tokens = list(mylang.lexer("a b c 10 8"))

state = State(mylang.implementation)
print(mylang.implementation['Z'])
print(mylang.named_parsers['Z'].match(tokens, state))
