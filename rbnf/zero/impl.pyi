from .user_interface import *
from rbnf.core.ParserC import Atom, Parser
from rbnf.core.Tokenizer import Tokenizer
from typing import Callable, Iterator, Dict
import typing
from Redy.Tools.PathLib import Path
import io

__all__ = ['compile', 'ResultDescription']


class ZeroExp:
    _top_parser: Parser
    _lexer: Callable[[str], Iterator[Tokenizer]]
    _lang: Dict[str, Parser]
    ctx: dict

    def __init__(self, bnf_syntax: str, use: str, custom_lexer_wrapper=None, language_name: str = None,
                 filename='<zero>'): ...

    def match(self, text) -> ResultDescription: ...

    def dumps(self) -> str:  ...

    def dump(self, file_repr: typing.Union[str, io.BufferedWriter]):
        if isinstance(file_repr, str):
            file_repr = Path(file_repr).open('w')

        with file_repr:
            file_repr.write(self.dumps())


def compile(bnf_syntax: str, use: str = None, custom_lexer_wrapper=None, language_name: str = None,
            filename=None) -> ZeroExp: ...
