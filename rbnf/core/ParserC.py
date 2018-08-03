from Redy.ADT import traits
from Redy.ADT.Core import RDT, data
from .Tokenizer import Tokenizer
from .AST import *
from .Result import *
from .State import *
from .._literal_matcher import *
from Redy.Magic.Pattern import Pattern
from Redy.Opt import feature, constexpr, const
from warnings import warn
import abc

staging = (const, constexpr)

Context = dict
LRFunc = Callable[[AST], Result]
When = Callable[[Sequence[Tokenizer], State], bool]
With = Callable[[Sequence[Tokenizer], State], bool]
Rewrite = Callable[[State], Named]


class ConsInd(traits.Ind):  # index following constructing
    def __getitem__(self: traits.IData, i):
        # noinspection PyUnresolvedReferences
        return self.__structure__[i] if self.__structure__ else self


class Parser(abc.ABC):
    def dumps(self):
        return self.dumps()

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

    def __rshift__(self, other: str):
        return Atom.Push(other, self)

    def __invert__(self):
        return Composed.AnyNot(self)

    def __matmul__(self, other: str):
        return Atom.Bind(other, self)

    def __repr__(self):
        return self.__sig_str__

    def __str__(self):
        return repr(self)

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

    def as_fixed(self, lang):
        return


@data
class Literal(Parser, ConsInd, traits.Dense, traits.Im):
    # match by regex
    # indeed it's stupid to use regex matching when parsing
    # (but regex is suitable for constructing lexers),
    # however RBNF supplies everything.
    R: RDT[lambda regex: [[make_regex_matcher(regex)], f'R{regex.__repr__()}']]

    # match by runtime string(equals)
    V: RDT[
        lambda runtime_str: [[make_runtime_str_matcher(runtime_str)], f'V{runtime_str.__repr__()}']]

    # match by name -> const string
    N: RDT[lambda name: [[make_name_matcher(name)], f'N{name.__repr__()}']]

    C: RDT[
        lambda const_string: [[make_const_str_matcher(const_string)], f'{const_string.__repr__()}']]

    NC: RDT[lambda name, const_string: [[make_name_and_const_str_matcher(name, const_string)],
                                        f'<{name}>{const_string.__repr__()}']]

    Invert: RDT[lambda literal: [[make_invert(literal)], f'~{literal}']]

    def match(self, tokenizers: Sequence[Tokenizer], state: State) -> Result:
        try:
            token = tokenizers[state.end_index]
        except IndexError:
            return Result.mismatched
        if self[1](token):
            state.new_one()
            return Result.match(token)
        return Result.mismatched

    def __invert__(self):
        # noinspection PyCallingNonCallable
        return Literal.Invert(self)


@data
class Atom(Parser, ConsInd, traits.Dense, traits.Im):
    Bind: lambda name, or_parser: f'({or_parser}) as {name}'
    Push: lambda name, or_parser: f'({or_parser}) to {name}'
    Named: RDT[
        lambda ref_name: [[ConstStrPool.cast_to_const(ref_name)], ref_name]]
    Any: '_'

    @Pattern
    def as_fixed(self, lang):
        addr = id(self)
        has_compile = lang['.has_compiled']
        if addr in has_compile:
            return None
        has_compile.add(addr)
        return self[0]

    @Pattern
    def match(self, tokenizers: Sequence[Tokenizer], state: State) -> Result:
        return self[0] if self.__structure__ else self


@data
class Composed(Parser, ConsInd, traits.Dense, traits.Im):
    And: lambda atoms: "({})".format(" ".join(map(str, atoms)))
    Or: lambda ands: "({})".format(" | ".join(map(str, ands)))
    Seq: lambda parser, least, most: f'({parser}){{{least} {most}}}'
    Jump: lambda switch_cases: "{{{}}}".format(
        ', '.join(f"({case.__repr__()} => {parser})" for case, parser in switch_cases.items()))

    AnyNot: lambda which: f'not {which}'

    @Pattern
    def as_fixed(self, lang):
        addr = id(self)
        has_compile = lang['.has_compiled']
        if addr in has_compile:
            return None
        has_compile.add(addr)
        return self[0]

    @Pattern
    def match(self, tokenizers: Sequence[Tokenizer], state: State) -> Result:
        return self[0]
