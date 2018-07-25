from rbnf.ParserC import *
from rbnf import ParserC
import abc
import typing

__all__ = ['Parser', 'Lexer', 'Language', 'auto_context']


class AutoContext:
    fn: 'function'


def auto_context(fn) -> AutoContext: ...


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

    @classmethod
    def bnf(cls):
        raise NotImplemented

    @classmethod
    def rewrite(cls, state: State):
        raise NotImplemented

    @classmethod
    def when(cls, tokens: Sequence[Tokenizer], state: State):
        raise NotImplemented

    @classmethod
    def fail_if(cls, tokens: Sequence[Tokenizer], state: State):
        raise NotImplemented


class Lexer(_ParserLike):

    @classmethod
    def regex(cls) -> typing.Sequence[str]:
        return []

    @classmethod
    def constants(cls) -> typing.Sequence[str]:
        return []

    @classmethod
    def cast(cls) -> bool:
        return False

    @classmethod
    def prefix(cls) -> typing.Optional[str]:
        return None


class Language:
    lexer: Callable[[str], Sequence[Tokenizer]]
    implementation: typing.Dict[str, typing.Union[Atom.Named, Literal.N]]
    prefix: typing.Dict[str, str]

    def __init__(self, lang_name: str): ...

    def __call__(self, *args, **kwargs) -> ParserC.Parser: ...

    def build(self): ...
