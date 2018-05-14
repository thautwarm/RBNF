from ebnf.State import *
from ebnf.ParserC import *


lit : Literal = Literal.C("1234"[:-1])
token = Tokenizer("no", ConstStrPool.cast_to_const("123"), 0, 1)
context = {}
tokens = [token]
state = State()

print(lit.match(tokens, state, context))


