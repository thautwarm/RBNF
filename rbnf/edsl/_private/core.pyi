import types

from rbnf.core.ParserC import *
from rbnf.core import ParserC
import abc
import typing

__all__ = ['Parser', 'Lexer', 'Language', 'auto_context', 'FnCodeStr']


class AutoContext:
    fn: 'function'


def auto_context(fn) -> AutoContext: ...


class FnCodeStr(typing.NamedTuple):
    code: str
    lineno: int
    colno: int
    filename: str
    namespace: dict
    fn_args = "tokens", "state"
    fn_name = ""


class _ParserLike(abc.ABC):
    lang: Language

    def match(self, tokenizers: Sequence[Tokenizer], state: State) -> Result:
        return self.match(tokenizers, state)

    def repeat(self, least, most=-1) -> 'Parser':
        return self(least, most)

    @property
    def one_or_more(self):
        return self.repeat(1, -1)

    @property
    def unlimited(self):
        return self.repeat(0)

    @property
    def optional(self):
        return self.repeat(0, 1)

    def __call__(self, least, most=-1) -> 'Parser':
        return Composed.Seq(self, least, most)

    def __invert__(self):
        return Composed.AnyNot(self)

    def __rshift__(self, other: str) -> Parser: ...

    def __matmul__(self, other: str):
        return Atom.Bind(other, self)

    def __or__(self, other):
        if self[0] is Composed.Or:
            if other[0] is Composed.Or:
                return Composed.Or([*self[1], *other[1]])
            return Composed.Or([*self[1], other])
        elif other[0] is Composed.Or:
            return Composed.Or([self, *other[1]])
        return Composed.Or([self, other])

    def __add__(self, other):
        if self[0] is Composed.And:
            if other[0] is Composed.And:
                return Composed.And([*self[1], *other[1]])
            return Composed.And([*self[1], other])
        elif other[0] is Composed.And:
            return Composed.And([self, *other[1]])
        return Composed.And([self, other])


class Parser(_ParserLike):

    @staticmethod
    def bnf():
        raise NotImplemented

    @staticmethod
    def rewrite(state: State):
        raise NotImplemented

    @staticmethod
    def when(tokens: Sequence[Tokenizer], state: State):
        raise NotImplemented

    @staticmethod
    def fail_if(tokens: Sequence[Tokenizer], state: State):
        raise NotImplemented


class Lexer(_ParserLike):

    @staticmethod
    def regex() -> typing.Sequence[str]:
        return []

    @staticmethod
    def constants() -> typing.Sequence[str]:
        return []

    @staticmethod
    def cast() -> bool:
        return False

    @staticmethod
    def prefix() -> typing.Optional[str]:
        return None


_nullable_fn = typing.Union[types.FunctionType]


class Language:
    lexer: Callable[[str], Sequence[Tokenizer]]
    named_parsers: typing.Dict[str, typing.Union[Atom.Named, Literal.N]]
    implementation: typing.Dict[str, typing.Tuple[ParserC.Parser, _nullable_fn, _nullable_fn, _nullable_fn]]

    prefix: typing.Dict[str, str]

    lang_name: str
    namespace = {}
    ignore_lst = {}

    def __init__(self, lang_name: str): ...

    def __call__(self, *args, **kwargs) -> ParserC.Parser: ...

    def build(self): ...

    def dumps(self) -> str: ...

    def ignore(self, *ignore_lst: str):
        """
        ignore a set of tokens with specific names
        """
        ...
