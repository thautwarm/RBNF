from Redy.Opt import constexpr, const, feature
from rbnf.core.Result import Result
from .user_interface import ResultDescription
import typing
import io
from Redy.Tools.PathLib import Path

__all__ = ['compile', 'ResultDescription']


class ZeroExp:
    def __init__(self,
                 bnf_syntax: str,
                 use: str,
                 custom_lexer_wrapper=None,
                 language_name=None,
                 filename="<zero>"):
        from rbnf.core.State import State
        from rbnf.bootstrap.rbnf import Language, build_language

        self._lang = ulang = Language(language_name or "ulang")
        build_language(bnf_syntax, ulang, filename)

        lexer, impl, namespace = ulang.lexer, ulang.implementation, ulang.namespace

        if use is None:
            try:
                top_parser = tuple(ulang.named_parsers.values())[-1]
            except IndexError:
                raise ValueError("No parser defined!")

        else:
            top_parser = ulang.named_parsers[use]

        @feature(const, constexpr)
        def match(text) -> ResultDescription:
            _wrapper: const = custom_lexer_wrapper
            _lexer: const = lexer

            _state = constexpr[State](constexpr[impl])

            _tokens = tuple(
                _wrapper(_lexer(text))
                if constexpr[custom_lexer_wrapper] else _lexer(text))

            _result: Result = constexpr[top_parser.match](_tokens, _state)

            return constexpr[ResultDescription](_state, _result.value, _tokens)

        self.match = match

    @property
    def lang(self):
        return self._lang

    def dumps(self):
        return self._lang.dumps()

    def dump(self, file_repr: typing.Union[str, io.TextIOWrapper, Path]):
        if isinstance(file_repr, str):
            return self.dump(Path(file_repr))

        if isinstance(file_repr, Path):
            return self.dump(file_repr.open('w'))

        with file_repr:
            file_repr.write(self.dumps())


def compile(bnf_syntax: str,
            use: str = None,
            custom_lexer_wrapper=None,
            language_name=None,
            filename="zero"):
    return ZeroExp(
        bnf_syntax,
        use,
        custom_lexer_wrapper=custom_lexer_wrapper,
        language_name=language_name,
        filename=filename)
