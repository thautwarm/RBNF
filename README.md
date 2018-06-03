# RBNF

Parser Generator for Context Sensitive Grammar
---------------------------------------------------

A sample of `rbnf`, see `tests` directory:
```
import std.common.[Name Space] 
# import `Name` and `Space` from $RBNF_HOME/std/common  

XML ::= 
    | '<' Name as t1 '/' '>'
    | '<' Name as t1 '>' (XML | ~('<' '/' Name '>'))* as seq '<' '/' 
    Name as t2 '>'
    with
        't2' not in state.ctx or t1.value == t2.value
    rewrite
        t1.value, seq if 'seq' in state.ctx else ()
```

You can also write EDSL in CPython, but there is no auto-lexer supplied for this mode.
```python
from rbnf.std.common import Name, Space # not equivalent to that of rbnf script
from rbnf.ParserC import *

def leave_constraint(tokens, state):
    ctx = state.ctx
    return 't2' not in ctx or ctx['t1'].value == ctx['t2'].value
def rewrite_xml(state):
    return ctx['t1'].value, ctx.get('seq', ())

language = {}

XML = Atom.Named('XML', None, leave_constraint, rewrite_xml)

impl_xml = ( # implement XML parser 
        C('<') + Name @ "t1" + C('>') + 
            (XML | ~('<' '/' Name '>'))* @ "seq" + 
        C('<') + C('/') + Name @ "t2"  + C('>') 
        |
        C('<') + Name @ "t1" + C('/') + C(">"))

language[XML[1]] = impl_xml

```



RBNF Bootstrap
----------------------------------------------

rbnf compiler is implemented by bootstrap, see [bootstrap embedded in CPython](https://github.com/thautwarm/Ruiko/blob/master/rbnf/std/rbnf_parser.py).


```
import std.common [*]

CodeItem ::= _  # any
        when
            sign.colno > tokens[state.end_index].colno

When ::= 'when' as sign CodeItem+ as expr
With ::= 'with' as sign CodeItem+ as expr
Rewrite ::= 'rewrite' as sign CodeItem+ as expr

Atom ::=
    | Name as name
    | Str as str
    | '(' Or as or ')'
    rewrite
        ctx = state.ctx
        if 'str' in ctx:
            r = ...
        elif 'name' in ctx:
            r = ...
        ...
        r

Trail ::=
    | Atom ['+' as one_or_more | '*' as zero_or_more | '{' Number{1 2} as interval'}'] ['as' Name as bind]
    | '~' as rev Atom
    rewrite
        <use context to build ASDL conveniently>
    


And   ::=
    | Trail+

Or    ::=
    | And ('|' And)* as seq

Statement ::=
    | 'import' Name ('.' ('*' | Name))* '.' '[' (* | Name+) ']'
    | Name '::=' ['|']  Or [When] [With] [Rewrite]
    | Name ['cast'] ['as' Name] ':=' Str+
    

Statements ::=
    | Statement (END Statement)* [END]
        
```

(README will be finished after my final exams.)