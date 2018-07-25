from rbnf.ParserC import *

__all__ = ['Parser', 'Lexer']


class _ParserLike(abc.ABC):

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
    @abc.abstractmethod
    def bnf():
        raise NotImplemented

    @staticmethod
    @abc.abstractmethod
    def rewrite(state: State):
        raise NotImplemented

    @staticmethod
    @abc.abstractmethod
    def when(tokens: Sequence[Tokenizer], state: State):
        raise NotImplemented

    @staticmethod
    @abc.abstractmethod
    def fail_if(tokens: Sequence[Tokenizer], state: State):
        raise NotImplemented

    pass


class Lexer(_ParserLike):
    @staticmethod
    @abc.abstractmethod
    def regex() -> typing.Sequence[str]:
        return []

    @staticmethod
    @abc.abstractmethod
    def constants() -> typing.Sequence[str]:
        return []

    @staticmethod
    @abc.abstractmethod
    def cast() -> bool:
        return False

    pass


class Lang:
    lexer: Callable[[str], Sequence[Tokenizer]]
    namespace: dict

    def __init__(self, lang_name: str): ...

    def build(self): ...
