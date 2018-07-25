import typing

from rbnf.std.edsl import Parser, Lexer, Language

lang = Language("number take")


@lang
class S12(Lexer):
    @staticmethod
    def constants() -> typing.Sequence[str]:
        return ["1", "2"]


@lang
class X(Parser):

    @staticmethod
    def bnf():
        return S12 + S12


lang.build()
print(list(lang.lexer("122")))

