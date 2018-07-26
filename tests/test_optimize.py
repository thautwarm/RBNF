from rbnf.ParserC import Literal, get_lexer_factors
from rbnf.Core.Optimize import optimize

AB = Literal.V("a") + Literal.V("b")
AC = Literal.V("a") + Literal.V("c")

AB_AC = AB | AC

assert optimize(AB_AC), Literal.V("a") == (Literal.V("b") | Literal.V("c"))


print(list(get_lexer_factors(AB_AC)))