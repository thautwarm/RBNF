from rbnf.core.ParserC import *
from rbnf.core.Tokenizer import Tokenizer
from Redy.Magic.Classic import cast


def test_jump():

    Case1 = Atom.Named("Case1")
    Case2 = Atom.Named("Case2")
    Case3 = Atom.Named("Case3")
    case1_impl = Literal.V(b"1") + Literal.V(b"2"), None, None, None
    case2_impl = Literal.V(b"a") + Literal.V(b"b"), None, None, None
    case3_impl = Literal.V(b"A") + Literal.V(b"B"), None, None, None

    lang = {"Case1": case1_impl, "Case2": case2_impl, "Case3": case3_impl}

    jump_parser: Parser = Composed.Jump({
        b"number": Case1,
        b"lower": Case2,
        b"upper": Case3
    })

    @cast(tuple)
    def make_tokens(*args):
        return map(lambda it: Tokenizer("too known", it, 0, 0), args)

    tokens = make_tokens(b"number", b"1", b"2", b"lower", b"a", b"b", b"upper",
                         b"A", b"B")

    print(jump_parser(1, -1).match(tuple(tokens), State(lang)))
