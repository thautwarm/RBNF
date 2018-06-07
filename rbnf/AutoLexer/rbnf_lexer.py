from . import *

StrLexerTable = List[Tuple[str, Callable[[str, int], str]]]

_keyword = ConstStrPool.cast_to_const("keyword")

_cast_map = set(
    map(ConstStrPool.cast_to_const, ["as", 'cast', 'when', 'where', 'with', 'rewrite', 'import', 'pyimport', 'ignore']))

_lexer_table: List[Tuple[str, Callable[[str, int], str]]] = [
    ("auto_const" | ToConst, char_lexer(('|', '{', '}', '[', ']', '(', ')', '+', '*', '.', ','))),
    ("auto_const" | ToConst, str_lexer(("::=", ":=", '<', '>', '/'))),

    ('Comment' | ToConst, regex_lexer(re.compile(r'(#.*)|(((/\*)+?[\w\W]+?(\*/)+))'))),
    ("Str" | ToConst, regex_lexer(re.compile(r'[A-Z]\'([^\\\']+|\\.)*?\'|\'([^\\\']+|\\.)*?\''))),
    ("Name" | ToConst, regex_lexer("[a-zA-Z_\u4e00-\u9fa5][a-zA-Z0-9_\u4e00-\u9fa5]*")), ("Number", regex_lexer("\d+")),

    ("Space" | ToConst, regex_lexer('\s+'))]

_Space = "Space" | ToConst
_END = "END" | ToConst
_UNKNOWN = 'Unknown' | ToConst
_DropTable = set(map(id, map(ConstStrPool.cast_to_const, ["Space"])))


def rbnf_lexing(text: str):
    cast_map = _cast_map
    lexer_table = _lexer_table
    keyword = _keyword
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

            address = id(name)
            if address not in _DropTable:
                if pat in cast_map:
                    yield Tokenizer(keyword, cast_const(pat), lineno, colno)
                else:
                    yield Tokenizer(cast_const(name), pat, lineno, colno)

            n = len(pat)
            line_inc = pat.count(newline)
            if line_inc:
                latest_newline_idx = pat.rindex(newline)
                colno = n - latest_newline_idx
                lineno += line_inc
                if name is _Space and pat[-1] == '\n':
                    yield Tokenizer(_END, '', lineno, colno)
            else:
                colno += n
            pos += n
            break
        else:
            char = text[pos]
            yield Tokenizer(_UNKNOWN, char, lineno, colno)
            pos += 1
            if char == '\n':
                lineno += 1
                colno = 0
            else:
                colno += 1
