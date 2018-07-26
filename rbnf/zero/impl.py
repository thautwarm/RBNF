from Redy.Opt import constexpr, const, feature
from rbnf.std.common import *
from rbnf.core.Tokenizer import Tokenizer
from rbnf.core.Result import Result
from rbnf.Color import Red, Green
from .user_interface import ResultDescription

__all__ = ['compile', 'ResultDescription']


class ZeroExp:
    def __init__(self, bnf_syntax: str, use: str, custom_lexer_wrapper=None, language_name=None):
        from rbnf.core.State import State
        from rbnf.bootstrap.rbnf import Language, build_language

        ulang = Language(language_name or "ulang")
        build_language(bnf_syntax, ulang)

        lexer, impl, namespace = ulang.lexer, ulang.implementation, ulang.namespace

        if use is None:
            try:
                top_parser = tuple(ulang.named_parsers.values())[-1]
            except:
                raise ValueError("No parser defined!")

        else:
            top_parser = ulang.named_parsers[use]
        @feature(const, constexpr)
        def match(text) -> ResultDescription:
            _state = constexpr[State](constexpr[impl])
            _wrapper: const = custom_lexer_wrapper
            _lexer: const = lexer
            _tokens = tuple(_wrapper(_lexer(text)) if constexpr[custom_lexer_wrapper] else _lexer(text))
            _result: Result = constexpr[top_parser.match](_tokens, _state)
            return constexpr[ResultDescription](_state, _result.value, _tokens)

        self.match = match


def compile(bnf_syntax: str, use: str = None, custom_lexer_wrapper=None, language_name=None):
    bnf_syntax = bnf_syntax
    return ZeroExp(bnf_syntax, use, custom_lexer_wrapper=custom_lexer_wrapper, language_name=language_name)
