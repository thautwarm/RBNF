from rbnf.edsl import Parser, Lexer, Language
from rbnf.err import LanguageBuildingError
from rbnf.core.State import State
from rbnf.core.Result import Result
from rbnf.core.Tokenizer import Tokenizer
import rbnf.zero as ze
import typing


def build_parser(lang: Language, opt=False, use_parser: str = None):
    from Redy.Opt import feature, constexpr, const
    from rbnf.core.ParserC import Atom
    if not lang.is_build:
        raise LanguageBuildingError("language haven't been built yet.")

    lexer, impl, namespace = lang.lexer, lang.implementation, lang.namespace

    if use_parser is None:
        try:
            top_parser = tuple(each for each in lang.named_parsers.values()
                               if isinstance(each, Atom))[-1]
        except IndexError:
            raise ValueError("No parser defined!")

    else:
        top_parser = lang.named_parsers[use_parser]
    if opt:
        lang.as_fixed()

    @feature(const, constexpr)
    def match(text) -> ze.ResultDescription:
        _lexer: const = lexer

        _state = constexpr[State](constexpr[impl])
        _tokens: typing.List[Tokenizer] = tuple(_lexer(text))

        _result: Result = constexpr[top_parser.match](_tokens, _state)

        return constexpr[ze.ResultDescription](_state, _result.value, _tokens)

    return match
