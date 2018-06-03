from rbnf.std.rbnf_parser import *
from rbnf import ParserC
from pprint import pprint
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

for each in tokens:
    print(each)
Z = ctx['Z']
print(ctx['lang']['Z'])
state = State(ctx['lang'])
print(ctx['Z'].match(tokens, state))

print(state.max_fetched)

# print(tuple(ctx['lex']('abc 4 a 2 a a 21')))
# print(ctx)


#
# res = tuple(rbnf_lexing("import std [Name It]"
#                         "X ::= a b c | d\n"
#                         "D ::= F g | e\n"
#                         "U cast as K := 'as' 'p'\n"
#                         "S ::= A (B as b) D as d (C as c)\n"
#                         "   when\n"
#                         "       x < 0\n"
#                         "   with\n"
#                         "       a.lineno = b.lineno + 2\n"
#                         ))
#
# stmts = Statements.match(res, State(bootstrap)).value
#
# for stmt in stmts:
#     print(stmt)
#
