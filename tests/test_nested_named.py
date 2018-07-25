from rbnf.ParserC import *
from Redy.Magic.Classic import cast

C = Literal.C


@cast(tuple)
def make_tokens(*args):
    return map(lambda it: Tokenizer("too known", it, 0, 0), args)


A = Atom.Named("A")

B = Atom.Named("B")

D = Atom.Named("C")

lang = {}

lang[A[1]] = C("1") + C("2") + B, None, None, None

lang[B[1]] = C("a") + C("b"), None, None, None

lang[D[1]] = A | B, None, None, None

print(D.match(make_tokens("1", "2", "a", "b"), State(lang)))
