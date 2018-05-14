from Redy.ADT.Core import data, RDT
from Redy.ADT import traits
from Redy.Magic.Pattern import Pattern
from Redy.Magic.Classic import singleton
from Redy.Typing import *
from .State import *
from .CachingPool import ConstStrPool
from .Tokenizer import Tokenizer
from ._literal_matcher import *
from .Result import *

Context = dict


@data
class Literal(traits.ConsInd, traits.Dense, traits.Im):
    # match by regex
    # indeed it's stupid to use regex matching when parsing, however EBNFParser supplies everything.
    R: RDT[lambda regex: [[make_regex_matcher(regex)], f'R{regex.__repr__()}']]

    # match by runtime string(equals)
    V: RDT[lambda runtime_str: [[make_runtime_str_matcher(runtime_str)], f'R{runtime_str.__repr__()}']]

    # match by name -> const string
    N: RDT[lambda name: [[make_name_matcher(name)], f'N{name.__repr__()}']]

    C: RDT[lambda const_string: [[make_const_str_matcher(const_string)], f'C{const_string.__repr__()}']]

    NC: RDT[lambda name, const_string: [[make_name_and_const_str_matcher(name, const_string)],
        f'<{name}>{const_string.__repr__()}']]

    Invert: RDT[lambda literal: [[lambda token: not literal[1](token)], f'~{literal}']]

    def __str__(self):
        return str(self.__inst_str__)

    def match(self, tokenizers: Sequence[Tokenizer], state: State, context: Context) -> Result:
        try:
            token = tokenizers[state.counted]
        except IndexError:
            return Result(Unmatched, None)
        if self[1](token):
            state.new_one()
            return Result(Matched, token)
        return Result(Unmatched, None)

    def __invert__(self):
        # noinspection PyCallingNonCallable
        return Literal.Invert(self)


class Atom:
    def __init__(self, ):
        pass
