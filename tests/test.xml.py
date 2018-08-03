import rbnf.zero as ze

ze_exp = ze.compile("""
import std.common.[Name Space] 
# import `Name` and `Space` from $RBNF_HOME/std/common  

XML ::= 
    | '<' Name as t1 '/' '>'
    | '<' Name as t1 '>' (XML | ~('<' '/' Name '>'))* as seq '<' '/'  Name as t2 '>'
    with
        't2' not in state.ctx or t1.value == t2.value
    rewrite
        t1.value, seq if 'seq' in state.ctx else ()
""")

print(ze_exp.match('<a> b </a>').result)