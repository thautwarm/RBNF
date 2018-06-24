from rbnf.AST import AST, Nested
from rbnf.ParserC import Literal, Context, Tokenizer, State, Atom as PAtom, Named
from rbnf.AutoLexer.rbnf_lexer import *
from rbnf.CachingPool import ConstStrPool
from rbnf.Optimize import optimize
from Redy.Tools.PathLib import Path
from Redy.Magic.Classic import singleton, record, execute
from typing import Sequence
from .common import Name, Str, Number, recover_codes
from linq.standard.list import Concat

ConstStrPool.cast_to_const('DefParser')
ToConst: ToConst


class IfNotNone:
    def __init__(self, func):
        self.func = func

    def __ror__(self, arg):
        return arg if arg is None else self.func(arg)


@singleton
class ToConst:
    def __ror__(self, item: str):
        return ConstStrPool.cast_to_const(item)


def code_item_enter_constraint(tokens: Sequence[Tokenizer], state: State):
    try:
        token = tokens[state.end_index]
    except IndexError:
        return False
    begin_sign: Tokenizer = state.ctx['sign']
    return token.colno > begin_sign.colno


class ASDL:

    def exports(self) -> Tuple:
        return self.exports()

    def requires(self) -> Tuple:
        return self.exports()


@record
class NameASDL(ASDL):
    value: str

    def __str__(self):
        return "N({})".format(repr(self.value))

    def requires(self):
        return self.value,

    def exports(self):
        return ()


@record
class ReverseASDL(ASDL):
    value: ASDL

    def __str__(self):
        return '(~{})'.format(self.value)

    def exports(self) -> Tuple:
        return self.value.exports()

    def requires(self) -> Tuple:
        return self.value.requires()


@record
class StrASDL(ASDL):
    value: str

    def __str__(self):
        if self.value.startswith('\''):
            return 'C({})'.format(self.value)
        else:
            prefix = self.value[0]
            value = self.value[1:]
            return '{}({})'.format(prefix, value)

    def requires(self):
        return ()

    def exports(self):
        if self.value.startswith('\'') or self.value.startswith('C\''):
            return ('auto_const', self.value, False),
        return ()


@record
class NameBindASDL(ASDL):
    body: ASDL
    name: str

    def __str__(self):
        return '({} @ {})'.format(self.body, repr(self.name))

    def exports(self):
        return self.body.exports()

    def requires(self):
        return self.body.requires()


@record
class RepeatASDL(ASDL):
    body: ASDL
    least: int
    most: int

    def exports(self):
        return self.body.exports()

    def requires(self):
        return self.body.requires()

    def __str__(self):
        return '({}.repeat({}, {}))'.format(self.body, self.least, self.most)


@record
class AndASDL(ASDL):
    value: Tuple[ASDL, ...]

    def exports(self):
        for each in map(ASDL.exports, self.value):
            yield from each

    def requires(self):
        for each in map(ASDL.requires, self.value):
            yield from each

    def __str__(self):
        return 'optimize({})'.join(' + '.join(map(str, self.value)))


@record
class OrASDL(ASDL):
    value: Tuple[ASDL, ...]

    def __str__(self):
        return 'optimize({})'.join(' | '.join(map(str, self.value)))

    def exports(self):
        for each in map(ASDL.exports, self.value):
            yield from each

    def requires(self):
        for each in map(ASDL.requires, self.value):
            yield from each


@record
class StmtsASDL(ASDL):
    value: Sequence[ASDL]

    def exports(self):
        for each in map(ASDL.exports, self.value):
            yield from each

    def requires(self):
        for each in map(ASDL.requires, self.value):
            yield from each

    def __str__(self):
        return '\n\n'.join(map(str, self.value))


@record
class IgnoreASDL(ASDL):
    names: Tuple[str, ...]

    def __str__(self):
        return 'ignore_lexer_names.append({})'.format(repr(self.names))


@record
class ImportASDL(ASDL):
    is_python_import: bool
    paths: Tuple[str, ...]
    import_items: Tuple[str, ...]

    def __str__(self):
        if self.is_python_import:
            from_ = '.'.join(self.paths)
            import_items = '*' if not self.import_items else ', '.join(self.import_items)
            return 'from {} import {}'.format(from_, import_items)

        from .compiler import parse
        with Path(*self.paths).open('r') as f:
            stmts = parse(f.read())
            asdls = stmts.value
        if not self.import_items:
            return '\n\n'.join(map(str, asdls))

        return '\n\n'.join(
                map(str, (each for each in asdls if hasattr(each, 'name') and each.name in self.import_items)))


@record
class ParserASDL(ASDL):
    name: str
    or_: OrASDL
    rewrite: str
    when: str
    with_: str

    def __str__(self):
        strs = []
        names = []
        for each in ['when', 'with_', 'rewrite']:
            attr = getattr(self, each)
            if attr:
                fn_name = '_{}_{}'.format(each, self.name)
                strs.append(make_fn(fn_name, attr))
                names.append(fn_name)
            else:
                names.append("None")

        strs.append('{} = __Atom.Named({}, {})'.format(self.name, repr(self.name), ','.join(names)))
        strs.append('_lang[{}] = {}'.format(repr(self.name), str(self.or_)))
        return '\n\n'.format(strs)

    def requires(self):
        return self.or_.requires()

    def exports(self):
        return self.or_.exports()


@record
class LexerASDL(ASDL):
    name: str
    is_const_cast: bool
    alias: str
    items: List['StrASDL']

    def __str__(self):
        if self.alias:
            return '{} = lambda str: NC({}, str)'.format(self.alias, repr(self.name))

    def exports(self):
        for each in self.
        return ((self.name, each[2:-1], True) if each.value.startswith('R\'') else (self.name, each.value[1:-1], False)
                for each in self.items)


def import_rewrite(state: State):
    ctx = state.ctx
    import_items = tuple(map(lambda it: it.value, ctx['import_items'])) if 'import_items' in ctx else None
    return ImportASDL('python' in ctx, (ctx['head'].value, *map(lambda it: it.value, ctx['tail'][1::2])), import_items)


def parser_rewrite(state: State):
    def try_get_first(x):
        if x:
            return x[0]
        return None

    name, or_, rewrite, when, with_ = map(state.ctx.__getitem__, ('name', 'or', 'rewrite', 'when', 'with'))
    return ParserASDL(name.value, or_, *map(try_get_first, (rewrite, when, with_)))


def lexer_rewrite(state: State):
    ctx = state.ctx
    name = ctx['name'].value
    is_const_cast = 'cast' in ctx
    alias = None if 'new prefix' not in ctx else ctx['new prefix'].value
    items = ctx['lexers']
    return LexerASDL(name, is_const_cast, alias, items)


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


def or_rewrite(state: State):
    ctx = state.ctx
    return OrASDL((ctx['head'], *ctx['tail'][1::2]))


def stmt_rewrite(state: State):
    ctx = state.ctx
    for _ in ('ignore', 'import', 'parser', 'lexer'):
        it = ctx.get(_, False)
        if it:
            return it


def postfix_rewrite(state: State):
    ctx = state.ctx
    expr = recover_codes(each.item for each in ctx['expr'])
    return expr


def ignore_rewrite(state: State):
    return IgnoreASDL(tuple(name.value for name in state.ctx['names']))
