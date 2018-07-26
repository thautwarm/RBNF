from typing import *
import typing
from .Tokenizer import Tokenizer
from .AST import *
from .Result import *
from .State import *
from .._literal_matcher import *

Context = dict
LRFunc = Callable[[AST], Result]
When = Callable[[Sequence[Tokenizer], State], bool]
With = Callable[[Sequence[Tokenizer], State], bool]
Rewrite = Callable[[State], Named]


class Parser:
    def match(self, tokenizers: Sequence[Tokenizer], state: State) -> Result:
        raise NotImplemented

    def repeat(self, least, most=-1) -> Parser:
        return self(least, most)

    def __getitem__(self, item) -> Any: ...

    def __call__(self, least, most=-1) -> Parser: ...

    def __invert__(self) -> Parser: ...

    def __rshift__(self, other: str) -> Parser: ...

    def __matmul__(self, other: str) -> Parser: ...

    def __or__(self, other) -> Parser: ...

    def __add__(self, other) -> Parser: ...

    @property
    def one_or_more(self) -> Parser:  ...

    @property
    def unlimited(self) -> Parser:  ...

    @property
    def optional(self) -> Parser:  ...


lit = Union[str, bytes]


class Literal(Parser):
    class R(Parser):
        def __new__(cls, regex: lit) -> Literal: ...

    class V(Parser):
        def __new__(cls, runtime_str: lit) -> Literal: ...

    class N(Parser):
        def __new__(cls, name: str) -> Literal: ...

    class C(Parser):
        def __new__(cls, const_str: lit) -> Literal: ...

    class NC(Parser):
        def __new__(cls, name: str, const_str: lit) -> Literal: ...

    class Invert(Parser):
        def __new__(cls, literal: Literal) -> Literal: ...

    def __invert__(self) -> Literal: ...

    def __getitem__(self, item) -> Any: ...


class Atom(Parser):
    class Bind(Parser):
        def __new__(cls, binding_name: str, or_parser: Parser) -> Atom: ...

    class Push(Parser):
        def __new__(cls, binding_name: str, or_parser: Parser) -> Atom: ...

    class Named(Parser):
        def __new__(cls, name: str, when: Optional[When], with_: Optional[With],
                    rewrite: Optional[Rewrite]) -> Atom: ...

    Any: Atom

    def __getitem__(self, item) -> typing.Any: ...


class Composed(Parser):
    class And(Parser):
        def __new__(cls, atoms: List[Atom]) -> Composed: ...

    class Or(Parser):
        def __new__(cls, ands: List[Composed]) -> Composed: ...

    class Seq(Parser):
        def __new__(cls, parser: Parser, least: int, most: int = 1) -> Composed: ...

    class Jump(Parser):
        def __new__(cls, switch_cases: Dict[lit, Parser]) -> Composed: ...

    class AnyNot(Parser):
        def __new__(cls, which: Parser) -> Composed: ...

    def __getitem__(self, item) -> Any: ...
