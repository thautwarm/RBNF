import typing

from rbnf.core.State import State
from rbnf.edsl import Parser, Lexer, Language, auto_context

lang = Language("number take")


@lang
class S12(Lexer):
    @classmethod
    def constants(cls) -> typing.Sequence[str]:
        return ["1", "2"]


@lang
class X(Parser):

    @classmethod
    def bnf(cls):
        return (S12 >> "f")(1, -1)

    @classmethod
    @auto_context
    def rewrite(cls, state: State):
        f: list
        return f


lang.build()
print(list(lang.lexer("122")))
print(X.match(tuple(lang.lexer("12")), State(lang.implementation)))
