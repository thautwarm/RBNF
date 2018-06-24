import os
from rbnf.std.compiler import *
from Redy.Tools.PathLib import Path

source_code = """
import std.common.[Name Space]
ignore [Space]
                
XML ::= 
    | '<' Name as t1 '/' '>'
    | '<' Name as t1 '>' (XML | ~('<' '/' Name '>'))* as seq '<' '/' Name as t2 '>'
    with
        not t2 or t1.value == t2.value
    rewrite
        t1.value, seq if seq else ()
"""

asdl = parse(source_code)
ctx = create_ctx()
visit(asdl, ctx)

tokens = tuple(ctx['lex']('<abc> bcd </efg>'))
state = State(ctx['lang'])
result = ctx['namespace']['XML'].match(tokens, state)
print(result)
assert result.status is Unmatched

tokens = tuple(ctx['lex']('<abc>'
                          '<nested>'
                          '<abc>'
                          'abc    '
                          '</abc></nested>'
                          '<single/>'
                          '</abc> '))
state = State(ctx['lang'])
result = ctx['namespace']['XML'].match(tokens, state)
print(result)
