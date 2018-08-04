def test_optimize():
    from rbnf.core.ParserC import Literal
    from rbnf.core.Optimize import optimize

    AB = Literal.V("a") + Literal.V("b")
    AC = Literal.V("a") + Literal.V("c")

    AB_AC = AB | AC

    assert optimize(AB_AC), Literal.V("a") == (Literal.V("b") | Literal.V("c"))
