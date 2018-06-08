from rbnf.AST import AST, Nested
from rbnf.ParserC import Literal, Context, Tokenizer, State, Atom as PAtom, Named
from rbnf.AutoLexer.rbnf_lexer import *
from rbnf.CachingPool import ConstStrPool
from rbnf.Optimize import optimize
from Redy.Magic.Classic import singleton, record, execute
from typing import Sequence
from .common import Name, Str, Number, recover_codes

ConstStrPool.cast_to_const('DefParser')


class IfNotNone:
    def __init__(self, func):
        self.func = func

    def __ror__(self, arg):
        return arg if arg is None else self.func(arg)


@singleton
class ToConst:
    def __ror__(self, item: str):
        return ConstStrPool.cast_to_const(item)


ToConst: ToConst

x: Tokenizer[str]
bootstrap = {}
C = Literal.C
N = Literal.N

END = N('END')


def code_item_enter_constraint(tokens: Sequence[Tokenizer], state: State):
    try:
        token = tokens[state.end_index]
    except IndexError:
        return False
    begin_sign: Tokenizer = state.ctx['sign']
    return token.colno > begin_sign.colno


class ASDL:
    pass


CodeItem = PAtom.Named("CodeItem", code_item_enter_constraint, None, None)


@record
class NameASDL(ASDL):
    value: str


@record
class ReverseASDL(ASDL):
    value: ASDL


@record
class StrASDL(ASDL):
    value: str


@record
class NameBindASDL(ASDL):
    body: ASDL
    name: str


@record
class RepeatASDL(ASDL):
    body: ASDL
    least: int
    most: int


@record
class AndASDL(ASDL):
    value: Tuple[ASDL, ...]


@record
class OrASDL(ASDL):
    value: Tuple[ASDL, ...]


@record
class StmtsASDL(ASDL):
    value: Sequence[ASDL]


def atom_rewrite(state: State):
    ctx = state.ctx
    body: ASDL = ctx.get('or')
    if not body:
        body = ctx.get('name') | IfNotNone(lambda it: NameASDL(it.value))
        if not body:
            body = ctx.get('str') | IfNotNone(lambda it: StrASDL(it.value))
            if not body:
                body = ctx.get('optional') | IfNotNone(lambda it: RepeatASDL(it, 0, 1))
    return body


AtomExpr = PAtom.Named("Atom", None, None, atom_rewrite)


def trail_rewrite(state: State):
    ctx = state.ctx
    atom = ctx['atom']

    @execute
    def ret():
        if 'rev' in ctx:
            return ReverseASDL(atom)
        if 'one_or_more' in ctx:
            return RepeatASDL(atom, 1, -1)
        if 'zero_or_more' in ctx:
            return RepeatASDL(atom, 0, -1)
        if 'interval' in ctx:
            interval: Nested = ctx['interval']
            if len(interval) is 1:
                least = int(interval[0].value)
                most = -1
            else:
                least, most = map(lambda it: int(it.value), ctx['interval'])
            return RepeatASDL(atom, least, most)
        return atom

    if 'bind' in ctx:
        return NameBindASDL(ret, ctx['bind'].value)
    return ret


Trail = PAtom.Named('Trail', None, None, trail_rewrite)


def and_rewrite(state: State):
    return AndASDL(state.ctx['value'])


And = PAtom.Named('And', None, None, and_rewrite)


def or_rewrite(state: State):
    ctx = state.ctx
    return OrASDL((ctx['head'], *ctx['tail'][1::2]))


Or = PAtom.Named('Or', None, None, or_rewrite)


def stmt_rewrite(state: State):
    ctx = state.ctx
    for _ in ('ignore', 'import', 'parser', 'lexer'):
        it = ctx.get(_, False)
        if it:
            return it


Statement = PAtom.Named('Statement', None, None, stmt_rewrite)


def stmts_rewrite(state: State):
    return StmtsASDL([e for e in state.ctx['seq'] if not isinstance(e, Tokenizer)])


def postfix_rewrite(state: State):
    ctx = state.ctx
    expr = recover_codes(each.item for each in ctx['expr'])
    return expr


Statements = PAtom.Named('Statements', None, None, stmts_rewrite)

When = PAtom.Named('When', None, None, postfix_rewrite)

With = PAtom.Named('With', None, None, postfix_rewrite)

Rewrite = PAtom.Named('Rewrite', None, None, postfix_rewrite)


@record
class IgnoreASDL(ASDL):
    names: Tuple[str, ...]


def ignore_rewrite(state: State):
    return IgnoreASDL(tuple(name.value for name in state.ctx['names']))


Ignore = PAtom.Named("Ignore", None, None, ignore_rewrite)


@record
class ImportASDL(ASDL):
    is_python_import: bool
    paths: Tuple[str, ...]
    import_items: Tuple[str, ...]


def import_rewrite(state: State):
    ctx = state.ctx
    import_items = tuple(map(lambda it: it.value, ctx['import_items'])) if 'import_items' in ctx else None
    return ImportASDL('python' in ctx, (ctx['head'].value, *map(lambda it: it.value, ctx['tail'][1::2])), import_items)


Import = PAtom.Named("Import", None, None, import_rewrite)


@record
class ParserASDL(ASDL):
    name: str
    or_: OrASDL
    rewrite: str
    when: str
    with_: str


def parser_rewrite(state: State):
    def try_get_first(x):
        if x:
            return x[0]
        return None

    name, or_, rewrite, when, with_ = map(state.ctx.__getitem__, ('name', 'or', 'rewrite', 'when', 'with'))
    return ParserASDL(name.value, or_, *map(try_get_first, (rewrite, when, with_)))


DefParser = PAtom.Named("DefParser", None, None, parser_rewrite)


@record
class LexerASDL(ASDL):
    name: str
    is_const_cast: bool
    alias: str
    items: List['StrASDL']


def lexer_rewrite(state: State):
    ctx = state.ctx
    name = ctx['name'].value
    is_const_cast = 'cast' in ctx
    alias = None if 'new prefix' not in ctx else ctx['new prefix'].value
    items = ctx['lexers']
    return LexerASDL(name, is_const_cast, alias, items)


DefLexer = PAtom.Named("DefLexer", None, None, lexer_rewrite)

bootstrap[CodeItem[1]] = PAtom.Any
bootstrap[When[1]] = C("when") @ "sign" + CodeItem.one_or_more @ "expr"
bootstrap[With[1]] = C("with") @ "sign" + CodeItem.one_or_more @ "expr"
bootstrap[Rewrite[1]] = C("rewrite") @ "sign" + CodeItem.one_or_more @ "expr"

bootstrap[AtomExpr[1]] = optimize(
        ((C('(') + Or @ "or" + C(')')) | (C('[') + Or @ "optional" + C(']')) | Name @ "name" | Str @ "str"))

bootstrap[Trail[1]] = optimize((C('~') @ "rev" + AtomExpr @ "atom" | AtomExpr @ "atom" + (
        C('+') @ "one_or_more" | C('*') @ "zero_or_more" | C('{') + Number(1, 2) @ "interval" + C('}')).optional) + (
                                       C('as') + Name @ "bind").optional)

bootstrap[And[1]] = Trail.one_or_more @ "value"

bootstrap[Or[1]] = optimize(And @ "head" + (C('|') + And).unlimited @ "tail")

import_syntax = optimize(
        (C('pyimport') @ "python" | C("import")) + Name @ "head" + (C('.') + (C('*') | Name)).unlimited @ "tail" + C(
                '.') + C('[') + (C('*') | Name.unlimited @ "import_items") + C(']'))

bootstrap[Import[1]] = optimize(import_syntax)

bootstrap[Ignore[1]] = optimize(C("ignore") + C('[') + Name.one_or_more @ "names" + C(']'))

parserc_syntax = Name @ "name" + C('::=') + C(
        '|').optional + Or @ "or" + When.optional @ "when" + With.optional @ "with" + Rewrite.optional @ "rewrite"
bootstrap[DefParser[1]] = optimize(parserc_syntax)

lexer_syntax = Name @ "name" + C('cast').optional @ "cast" + (C('as') + Name @ "new prefix").optional + C(':=') + C(
        '|').optional + Str.one_or_more @ "lexers"
bootstrap[DefLexer[1]] = optimize(lexer_syntax)

bootstrap[Statement[1]] = Ignore @ "ignore" | Import @ "import" | DefParser @ "parser" | DefLexer @ "lexer"
bootstrap[Statements[1]] = optimize(END.optional + (Statement + END.optional).unlimited @ "seq")
