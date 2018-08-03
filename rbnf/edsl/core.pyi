from .rbnf_analyze import *
from rbnf.core import ParserC
from rbnf.core.ParserC import State, Literal, ConstStrPool
from rbnf.core.Result import Result
from rbnf.core.Tokenizer import Tokenizer
from rbnf.err import LanguageBuildingError
from rbnf.auto_lexer import lexing
from rbnf.py_tools.unparse import Unparser
from collections import OrderedDict, defaultdict
from Redy.Opt import Macro, feature, constexpr, const
from Redy.Opt import get_ast
from Redy.Magic.Classic import cast
from Redy.Typing import T1, T2
from typing import Sequence
import abc
import ast
import typing
import types
import textwrap
import builtins
import io
import warnings

__all__ = ['Parser', 'Lexer', 'Language', 'auto_context', '_FnCodeStr']


class AutoContext:
    fn: 'function'


def auto_context(fn) -> AutoContext:
    ...


class _FnCodeStr(typing.NamedTuple):
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
        ...

    @property
    def one_or_more(self) -> Parser:
        ...

    @property
    def unlimited(self) -> Parser:
        ...

    @property
    def optional(self) -> Parser:
        ...

    def __call__(self, least, most=-1) -> 'Parser':
        ...

    def __invert__(self) -> Parser:
        ...

    def __rshift__(self, other: str) -> Parser:
        ...

    def __matmul__(self, other: str) -> Parser:
        ...

    def __or__(self, other) -> Parser:
        ...

    def __add__(self, other) -> Parser:
        ...


class OrderedDefaultDict(OrderedDict):
    cons: typing.Callable

    def set_factory(self, cons):
        self.cons = cons

    def __missing__(self, key):
        value = self[key] = self.cons()
        return value


class CamlMap(typing.Mapping[T1, T2]):
    def __init__(self):
        self._ = []

    def __getitem__(self, item):
        for k, v in reversed(self._):
            if k == item:
                return v
        raise KeyError(item)

    def __setitem__(self, key, value):
        self._.append((key, value))

    def __len__(self):
        return len(self._)

    def __iter__(self):
        for k, _ in self._:
            yield k

    def items(self):
        for each in self._:
            yield each


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


_nullable_fn = typing.Optional[types.FunctionType]


class Language:
    lexer: typing.Callable[[str], Sequence[Tokenizer]]
    named_parsers: CamlMap[str, typing.Union[ParserC.Atom.Named,
                                             ParserC.Literal.N]]
    implementation: typing.Dict[str, typing.Tuple[ParserC.Parser, _nullable_fn,
                                                  _nullable_fn, _nullable_fn]]
    prefix: typing.Dict[str, str]
    lang_name: str
    namespace = {}
    ignore_lst = {}
    dump_spec: CamlMap[str, typing.Tuple[str]]

    def __init__(self, lang_name: str):
        ...

    def __call__(self, *args, **kwargs) -> ParserC.Parser:
        ...

    @property
    def is_build(self) -> bool:
        ...

    def build(self):
        ...

    def dump(self, filename: str):
        ...

    def dumps(self) -> str:
        ...

    def as_fixed(self) -> None:
        """
        optimize the parser and make it static.
        after `as_fixed` you cannot change the implementation of a named parser dynamically.
        """
        ...

    def ignore(self, *ignore_lst: str):
        """
        ignore a set of tokens with specific names
        """
        ...
