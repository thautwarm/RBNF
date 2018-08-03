from .user_interface import *
from rbnf.core.ParserC import Atom, Parser
from rbnf.core.Tokenizer import Tokenizer
from typing import Callable, Iterator, Dict
from Redy.Tools.PathLib import Path
from rbnf.edsl.core import Language
import typing
import io

__all__ = ['compile', 'ResultDescription']


class ZeroExp:
    _top_parser: Parser
    _lexer: Callable[[str], Iterator[Tokenizer]]
    _lang: Language
    ctx: dict

    def __init__(self,
                 bnf_syntax: str,
                 use: str,
                 custom_lexer_wrapper=None,
                 language_name: str = None,
                 filename='<zero>'):
        ...

    @property
    def lang(self) -> Language:
        ...

    def match(self, text) -> ResultDescription:
        ...

    def dumps(self) -> str:
        ...

    def dump(self, file_repr: typing.Union[str, Path, io.BufferedWriter]):
        ...


def compile(bnf_syntax: str,
            use: str = None,
            custom_lexer_wrapper=None,
            language_name: str = None,
            filename=None) -> ZeroExp:
    ...
