from rbnf.ParserC import *
from rbnf.AutoLexer import str_lexer, regex_lexer
import typing

__all__ = ['get_binding_names', 'get_lexer_factors', 'RegexLexerFactor', 'ConstantLexerFactor']


class RegexLexerFactor(typing.NamedTuple):
    name: str
    factors: typing.List[str]

    def to_lexer(self):
        print(self.name, self.factors)
        return self.name, regex_lexer(self.factors)


class ConstantLexerFactor(typing.NamedTuple):
    name: str
    factors: typing.List[str]

    def to_lexer(self):
        print(self.name, self.factors)
        return self.name, str_lexer(self.factors)


def get_lexer_factors(parser: 'Parser') -> typing.Generator[
    typing.Union[RegexLexerFactor, ConstantLexerFactor], None, None]:
    def for_literal(lit: Literal):
        if lit[0] is Literal.R:
            a, b = lit[1].raw
            yield RegexLexerFactor(a, [b])

        elif lit[0] in (Literal.C, Literal.NC):
            a, b = lit[1]
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

        else:
            for each in map(get_lexer_factors, comp[1]):
                yield from each

    return {
        Literal: for_literal, Atom: for_atom, Composed: for_composed
    }[type(parser)](parser)


def get_binding_names(parser: 'Parser') -> typing.Generator[str, None, None]:
    def for_literal(_):
        return ()

    def for_atom(atom: Atom):
        if Atom.Bind is atom[0]:
            return atom[1],
        if Atom.Push is atom[0]:
            return atom[1],
        return ()

    def for_composed(comp: Composed):
        if comp[0] is Composed.Jump:
            for each in map(get_binding_names, comp[1].values()):
                yield from each
        elif comp[0] is Composed.Seq:
            yield from get_binding_names(comp[1])

        else:
            for each in map(get_binding_names, comp[1]):
                yield from each

    return {
        Literal: for_literal, Atom: for_atom, Composed: for_composed
    }[type(parser)](parser)
