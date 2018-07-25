"""
Current module is archived with PEP8 rules broken.
"""
from Redy.Opt import feature, const, constexpr
staging = (const, constexpr)
from . import *

StrLexerTable = List[Tuple[str, Callable[[str, int], str]]]
_keyword = ConstStrPool.cast_to_const("keyword")

_cast_map = set(
    map(ConstStrPool.cast_to_const, ["as", 'cast', 'when', 'with', 'rewrite', 'import', 'pyimport', 'ignore', 'to']))

_lexer_table: List[Tuple[str, Callable[[str, int], str]]] = [
    ("auto_const" | ToConst,  char_lexer(('|', '{', '}', '[', ']', '(', ')', '+', '*', '.', ','))),
    ("auto_const" | ToConst,  str_lexer(("::=", ":=", '<', '>', '/'))),
    ("Str"        | ToConst,  regex_lexer(re.compile(r'[A-Z]\'([^\\\']+|\\.)*?\'|\'([^\\\']+|\\.)*?\''))),
    ("Name"       | ToConst,  regex_lexer("[a-zA-Z_\u4e00-\u9fa5][a-zA-Z0-9_\u4e00-\u9fa5]*")), ("Number", regex_lexer("\d+")),
    ("Space"      | ToConst,  regex_lexer('\s+')),
    ('Comment'    | ToConst,  regex_lexer(re.compile(r'(#.*)|(((/\*)+?[\w\W]+?(\*/)+))'))),]

_Space     = "Space"   | ToConst
_END       = "END"     | ToConst
_UNKNOWN   = 'Unknown' | ToConst
_DropTable = {id(each  | ToConst) for each in ('Space', 'Comment')}


@feature(staging)
def rbnf_lexing(text: str):
    """Read loudly for documentation."""

    cast_map: const    = _cast_map
    lexer_table: const = _lexer_table
    keyword: const     = _keyword
    drop_table: const  = _DropTable
    end: const         = _END
    unknown: const     = _UNKNOWN

    text_length = len(text)
    colno       = 0
    lineno      = 0
    position    = 0

    cast_const  = ConstStrPool.cast_to_const

    while True:
        if text_length <= position:
            break

        for case_name, text_match_case in lexer_table:

            matched_text = text_match_case(text, position)

            if not matched_text:
                continue

            case_mem_addr = id(case_name)  # memory address of case_name

            if case_mem_addr not in drop_table:

                if matched_text in cast_map:
                    yield Tokenizer(keyword, cast_const(matched_text), lineno, colno)

                else:
                    yield Tokenizer(cast_const(case_name), matched_text, lineno, colno)

            n = len(matched_text)
            line_inc = matched_text.count('\n')

            if line_inc:

                latest_newline_idx = matched_text.rindex('\n')
                colno = n - latest_newline_idx
                lineno += line_inc

                if case_name is _Space and matched_text[-1] == '\n':

                    yield Tokenizer(end, '', lineno, colno)

            else:
                colno += n
            position += n
            break

        else:

            char = text[position]
            yield Tokenizer(unknown, char, lineno, colno)

            position += 1

            if char == '\n':
                lineno += 1
                colno = 0

            else:
                colno += 1
