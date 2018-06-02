from rbnf.drive_syntax.rbnf_parser import *

res = tuple(rbnf_lexing("X ::= a b c | d\n"
                        "D ::= F g | e\n"
                        "U cast as K := 'as' 'p'\n"
                        "S ::= X \n"
                        "    with \n"
                        "    <lang> python </lang>\n"
                        "    <code> ... </code>"))
for each in res:
    print(each)

print(Statements.match(res, State(bootstrap)))
