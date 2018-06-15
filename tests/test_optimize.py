from rbnf.ParserC import Literal, Context, Tokenizer, State, Atom as PAtom
from rbnf.AutoLexer.rbnf_lexer import *
from rbnf.CachingPool import ConstStrPool
from rbnf.Optimize import optimize

AB = Literal.V("a") + Literal.V("b")
AC = Literal.V("a") + Literal.V("c")

AB_AC = AB | AC

assert optimize(AB_AC), Literal.V("a") == (Literal.V("b") | Literal.V("c"))

