from ..ParserC import Literal, Tokenizer
from typing import Iterator

N = Literal.N
Name = N('Name')
Str = N('Str')
Number = N('Number')


def recover_codes(tokens: Iterator[Tokenizer]):
    """
    from a series of tokenizers to code string. (preserve the indentation)
    """
    tokens = iter(tokens)

    s = []
    head = next(tokens)
    lineno = head.lineno
    start_indent = colno = head.colno
    s.append(head.value)
    colno += len(s[-1])
    for each in tokens:
        n = each.lineno - lineno
        if n:
            s.append('\n' * n)
            lineno = each.lineno
            colno = each.colno
            if colno - start_indent > 0:
                s.append(' ' * colno)
        else:
            c = each.colno - colno
            if c:
                colno = each.colno
                if c > 0:
                    s.append(' ' * c)
        s.append(each.value)
        colno += len(s[-1])
    return ''.join(s)


def underline_mangling(name: str):
    return name.replace('_', '__')
