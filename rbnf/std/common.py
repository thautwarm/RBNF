from Redy.Magic.Classic import cast
from ..core.ParserC import Literal, Tokenizer
from typing import Iterator

N = Literal.N
Name = N('Name')
Str = N('Str')
Number = N('Number')


# noinspection PyTypeChecker
@cast(''.join)
def recover_codes(tokens: Iterator[Tokenizer]) -> str:
    """
    from a series of tokenizers to code string. (preserve the indentation)
    """

    tokens = iter(tokens)

    s = []

    try:
        head = next(tokens)

    except StopIteration:
        return s

    append = s.append
    lineno = head.lineno

    start_indent = colno = head.colno

    append(head.value)

    colno += len(s[-1])

    for each in tokens:
        n = each.lineno - lineno

        if n:
            append('\n' * n)
            lineno = each.lineno
            colno = each.colno

            if colno - start_indent > 0:
                append(' ' * colno)

        else:
            c = each.colno - colno
            if c:
                colno = each.colno
                if c > 0:
                    append(' ' * c)

        append(each.value)

        colno += len(s[-1])

    return s


def underline_mangling(name: str):
    return name.replace('_', '__')
