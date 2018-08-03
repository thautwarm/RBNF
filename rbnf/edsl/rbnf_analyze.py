from rbnf.core.ParserC import *
from rbnf.core.Tokenizer import Tokenizer
from rbnf.core.CachingPool import ConstStrPool
from rbnf.auto_lexer import str_lexer, regex_lexer

import typing
from Redy.Magic.Pattern import Pattern as _Pat

__all__ = [
    'get_binding_names', 'get_lexer_factors', 'RegexLexerFactor',
    'ConstantLexerFactor', 'dumps', 'check_parsing_complete'
]


class RegexLexerFactor(typing.NamedTuple):
    name: str
    factors: typing.List[str]

    def to_lexer(self):
        # print("making regex lexers:", self.name, self.factors)
        return ConstStrPool.cast_to_const(self.name), regex_lexer(self.factors)


class ConstantLexerFactor(typing.NamedTuple):
    name: str
    factors: typing.List[str]

    def to_lexer(self):
        # print("making constant lexers: ", self.name, self.factors)
        return ConstStrPool.cast_to_const(self.name), str_lexer(self.factors)


def get_lexer_factors(parser: 'Parser') -> typing.Generator[typing.Union[
        RegexLexerFactor, ConstantLexerFactor], None, None]:
    def for_literal(lit: Literal):
        if lit[0] is Literal.R:
            a, b = lit[1].raw
            yield RegexLexerFactor(a, [b])

        elif lit[0] in (Literal.C, Literal.NC):
            a, b = lit[1].raw
            yield ConstantLexerFactor(a, [b])

        else:
            return

    def for_atom(atom: Atom):
        if Atom.Bind is atom[0]:
            yield from get_lexer_factors(atom[2])
        if Atom.Push is atom[0]:
            yield from get_lexer_factors(atom[2])
        return

    def for_composed(comp: Composed):
        if comp[0] is Composed.Jump:
            for each in map(get_lexer_factors, comp[1].values()):
                yield from each
        elif comp[0] is Composed.Seq:
            yield from get_lexer_factors(comp[1])
        elif comp[0] is Composed.AnyNot:
            yield from get_lexer_factors(comp[1])
        else:
            for each in map(get_lexer_factors, comp[1]):
                yield from each

    return {
        Literal: for_literal,
        Atom: for_atom,
        Composed: for_composed
    }[type(parser)](parser)


def get_binding_names(parser: 'Parser') -> typing.Generator[str, None, None]:
    def for_literal(_):
        return ()

    def for_atom(atom: Atom):
        if Atom.Bind is atom[0]:
            yield atom[1]
            yield from get_binding_names(atom[2])

        elif Atom.Push is atom[0]:
            yield atom[1]
            yield from get_binding_names(atom[2])

    def for_composed(comp: Composed):
        if comp[0] is Composed.Jump:
            for each in map(get_binding_names, comp[1].values()):
                yield from each
        elif comp[0] is Composed.Seq:
            yield from get_binding_names(comp[1])

        elif comp[0] is Composed.AnyNot:
            yield from get_binding_names(comp[1])

        else:
            for each in map(get_binding_names, comp[1]):
                yield from each

    return {
        Literal: for_literal,
        Atom: for_atom,
        Composed: for_composed
    }[type(parser)](parser)


@_Pat
def dumps(parser):
    return type(parser)


_NAME = 0
_VALUE = 1


@dumps.case(Literal)
def dumps(self):
    tag = self[0]
    if tag is Literal.R:
        return f"ruiko.R({self[1].raw[_VALUE]!r})"
    if tag is Literal.V:
        return f"ruiko.V({self[1].raw[_VALUE]!r})"
    if tag is Literal.N:
        return f"ruiko.N({self[1].raw[_NAME]!r})"
    if tag is Literal.C:
        return f"ruiko.C({self[1].raw[_VALUE]!r})"
    if tag is Literal.NC:
        name, value = self[1].raw
        return f"ruiko.NC({name!r}, {value!r})"
    if tag is Literal.Invert:
        return f"~{dumps(self[1].raw)}"
    raise TypeError(tag)


@dumps.case(Atom)
def dumps(self):
    tag = self[0]
    if tag is Atom.Bind:
        _, name, or_parser = self
        return f"ruiko.Bind({name!r}, {dumps(or_parser)})"
    if tag is Atom.Push:
        _, name, or_parser = self
        return f"ruiko.Push({name!r}, {dumps(or_parser)})"
    if tag is Atom.Named:
        _, name = self
        return f"ruiko.Named({name!r})"
    if tag is Atom.Any:
        return f"ruiko.Any"
    raise TypeError(tag)


@dumps.case(Composed)
def dumps(self):
    tag = self[0]

    if tag is Composed.And:
        atoms = self[1]
        return "ruiko.And([{}])".format(",".join(map(dumps, atoms)))

    if tag is Composed.Or:
        ands = self[1]
        return "ruiko.Or([{}])".format(",".join(map(dumps, ands)))

    if tag is Composed.Seq:
        _, parser, least, most = self
        return "ruiko.Seq({}, {!r}, {!r})".format(dumps(parser), least, most)

    if tag is Composed.Jump:
        dictionary = ", ".join(
            "{!r}: {}".format(k, dumps(v)) for k, v in self[1].items())
        return "ruiko.Jump({})".format(dictionary)

    if tag is Composed.AnyNot:
        return "ruiko.AnyNot({})".format(dumps(self[1]))
    raise TypeError(tag)


def check_parsing_complete(source_code: str, tokens: Sequence[Tokenizer],
                           state: State):
    def _find_nth(string: str, element, nth: int = 0):
        _pos: int = string.find(element)
        if _pos is -1:
            return 0

        while nth:
            _pos = string.index(element, _pos) + 1
            nth -= 1
        return _pos

    if not tokens:
        raise SyntaxError("Error occurred at the first character "
                          "in file {}, see details:\n{}".format(
                              state.filename, Red(source_code[:20])))

    if state.end_index < len(tokens):
        max_fetched = state.max_fetched
        if max_fetched >= len(tokens):
            tk = tokens[-1]
            err_description = 'Incomplete syntax'
        else:
            tk: Tokenizer = tokens[max_fetched]
            err_description = 'Error'
        lineno, colno = tk.lineno, tk.colno
        pos = _find_nth(source_code, '\n', lineno) + colno
        before = source_code[max(0, pos - 25):pos]
        later = source_code[pos:min(pos + 25, len(source_code))]

        raise SyntaxError("{} at line {}, col {} in file {}, see details:\n"
                          "{}".format(err_description, tk.lineno, tk.colno,
                                      state.filename,
                                      Green(before) + Red(later)))
