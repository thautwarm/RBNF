from ..Tokenizer import Tokenizer
from ..CachingPool import ConstStrPool
from ..Color import *
from typing import *
from Redy.Magic.Pattern import Pattern
from Redy.Magic.Classic import singleton
from warnings import warn
import re


@singleton
class ToConst:
    def __ror__(self, item: str):
        return ConstStrPool.cast_to_const(item)


ToConst: ToConst

lit = Union[bytes, str]
T = TypeVar('T')
LexerTable = List[Tuple[T, Callable[[T, int], T]]]
# LexerTable : [(str, str -> str)]

StrLexerTable = List[Tuple[str, Callable[[str, int], str]]]
BytesLexerTable = List[Tuple[str, Callable[[bytes, int], bytes]]]
DropTable = Set[int]
CastMap = Dict[str, str]
_UNKNOWN = "Unknown" | ToConst


@Pattern
def lexing(text: lit, lexer_table: LexerTable, cast_map: CastMap) -> Iterable[Tokenizer[lit]]:
    return type(text), bool(cast_map)


@lexing.case((bytes, True))
def lexing(text: bytes, lexer_table: BytesLexerTable, cast_map: CastMap):
    text_length = len(text)
    colno = 0
    lineno = 0
    pos = 0
    newline = b'\n'
    cast_const = ConstStrPool.cast_to_const
    while True:
        if text_length <= pos:
            break

        for name, case in lexer_table:
            pat = case(text, pos)
            if not pat:
                continue
            if pat in cast_map:
                yield Tokenizer(cast_map[pat], cast_const(pat), lineno, colno)
            else:
                yield Tokenizer(name, pat, lineno, colno)
            n = len(pat)
            line_inc = pat.count(newline)
            if line_inc:
                latest_newline_idx = pat.rindex(newline)
                colno = n - latest_newline_idx
                lineno += line_inc
            else:
                colno += n
            pos += n
            break

        else:
            warn(Yellow(f"No handler for character `{text[pos].__repr__()}`."))
            chr = text[pos]
            yield Tokenizer(_UNKNOWN, chr, lineno, colno)
            if text[pos] == '\n':
                lineno += 1
                colno = 0
            pos += 1


@lexing.case((str, True))
def lexing(text: str, lexer_table: StrLexerTable, cast_map: CastMap = None):
    text_length = len(text)
    colno = 0
    lineno = 0
    pos = 0
    newline = '\n'
    cast_const = ConstStrPool.cast_to_const
    while True:
        if text_length <= pos:
            break

        for name, case in lexer_table:
            pat = case(text, pos)
            if not pat:
                continue
            if pat in cast_map:
                yield Tokenizer(cast_map[pat], cast_const(pat), lineno, colno)
            else:
                yield Tokenizer(name, pat, lineno, colno)
            n = len(pat)
            line_inc = pat.count(newline)
            if line_inc:
                latest_newline_idx = pat.rindex(newline)
                colno = n - latest_newline_idx
                lineno += line_inc
            else:
                colno += n
            pos += n
            break

        else:
            warn(Yellow(f"No handler for character `{text[pos].__repr__()}`."))
            char = text[pos]
            yield Tokenizer(_UNKNOWN, char, lineno, colno)
            if char == '\n':
                lineno += 1
                colno = 0
            pos += 1


@lexing.case((str, False))
def lexing(text: str, lexer_table: StrLexerTable, _):
    text_length = len(text)
    colno = 0
    lineno = 0
    pos = 0
    newline = '\n'
    while True:
        if text_length <= pos:
            break

        for name, case in lexer_table:
            pat = case(text, pos)
            if not pat:
                continue
            yield Tokenizer(name, pat, lineno, colno)
            n = len(pat)
            line_inc = pat.count(newline)
            if line_inc:
                latest_newline_idx = pat.rindex(newline)
                colno = n - latest_newline_idx
                lineno += line_inc
            else:
                colno += n
            pos += n
            break

        else:
            warn(Yellow(f"No handler for character `{text[pos].__repr__()}`."))
            chr = text[pos]
            yield Tokenizer(_UNKNOWN, chr, lineno, colno)
            if text[pos] == '\n':
                lineno += 1
                colno = 0
            pos += 1


@lexing.case((bytes, False))
def lexing(text: bytes, lexer_table: BytesLexerTable, _):
    text_length = len(text)
    colno = 0
    lineno = 0
    pos = 0
    newline = b'\n'
    cast_const = ConstStrPool.cast_to_const
    while True:
        if text_length <= pos:
            break

        for name, case in lexer_table:
            pat = case(text, pos)
            if not pat:
                continue
            yield Tokenizer(name, pat, lineno, colno)
            n = len(pat)
            line_inc = pat.count(newline)
            if line_inc:
                latest_newline_idx = pat.rindex(newline)
                colno = n - latest_newline_idx
                lineno += line_inc
            else:
                colno += n
            pos += n
            break
        else:
            warn(Yellow(f"No handler for character `{text[pos].__repr__()}`."))
            chr = text[pos]
            yield Tokenizer(_UNKNOWN, chr, lineno, colno)
            if text[pos] == '\n':
                lineno += 1
                colno = 0
            pos += 1


def char_lexer(mode):
    """
    a faster way for characters to generate token strings cache
    """

    def f_raw(inp_str, pos):
        return mode if inp_str[pos] is mode else None

    def f_collection(inp_str, pos):
        ch = inp_str[pos]
        for each in mode:
            if ch is each:
                return ch
        return None

    if isinstance(mode, str):
        return f_raw

    if len(mode) is 1:
        mode = mode[0]
        return f_raw

    return f_collection


def str_lexer(mode):
    """
    generate token strings' cache
    """
    cast_to_const = ConstStrPool.cast_to_const
    def f_raw(inp_str, pos):
        return cast_to_const(mode) if inp_str.startswith(mode, pos) else None

    def f_collection(inp_str, pos):
        for each in mode:
            if inp_str.startswith(each, pos):
                return cast_to_const(each)
        return None

    if isinstance(mode, str):
        return f_raw

    if len(mode) is 1:
        mode = mode[0]
        return f_raw

    return f_collection


def regex_lexer(regex_pat):
    """
    generate token names' cache
    """

    if isinstance(regex_pat, str):
        regex_pat = re.compile(regex_pat)

        def f(inp_str, pos):
            m = regex_pat.match(inp_str, pos)
            return m.group() if m else None
    elif hasattr(regex_pat, 'match'):
        def f(inp_str, pos):
            m = regex_pat.match(inp_str, pos)
            return m.group() if m else None
    else:
        regex_pats = tuple(re.compile(e) for e in regex_pat)

        def f(inp_str, pos):
            for each_pat in regex_pats:
                m = each_pat.match(inp_str, pos)
                if m:
                    return m.group()

    return f
