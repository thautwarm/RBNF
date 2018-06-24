from rbnf.std.rbnf_parser import *
from rbnf.std.compiler import parse, visit, create_ctx

asdls = parse("""
Space := R'\s'
Name := R'[a-zA-Z]+'
Alpha cast := 'a' 'b' 'c'

Num := R'\d+'
Z ::= Alpha+ Num as n1 Num as n2
    with
        d1 = int(n1.value)
        d2 = int(n2.value)
        d1 > d2
""")

ctx = create_ctx()
visit(asdls, ctx)
tokens = tuple(e for e in ctx['lex']('a b c 10 8') if e.name != 'Space')


state = State(ctx['lang'])
print(ctx['namespace']['Z'].match(tokens, state))
