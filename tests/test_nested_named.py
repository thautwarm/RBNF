from rbnf.ParserC import *
from Redy.Magic.Classic import cast

C = Literal.C


@cast(tuple)
def make_tokens(*args):
    return map(lambda it: Tokenizer("too known", it, 0, 0), args)


A = Atom.Named("A", None, None, None)

B = Atom.Named("B", None, None, None)

D = Atom.Named("C", None, None, None)

lang = {}

lang[A[1]] = C("1") + C("2") + B

lang[B[1]] = C("a") + C("b")

lang[D[1]] = A | B

print(D.match(make_tokens("1", "2", "a", "b"), State(lang)))
