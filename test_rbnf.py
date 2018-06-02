from rbnf.drive_syntax.rbnf_parser import *

res = tuple(rbnf_lexing("\n"
                        "X ::= a b c | d\n"
                        "D ::= F g | e\n"
                        "U cast as K := 'as' 'p'\n"))

print(Statements.match(res, State(lang)))
