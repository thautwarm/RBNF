import itertools

from .rbnf_parser import *
from ..AutoLexer import lexing
from ..ParserC import *
from Redy.Magic.Pattern import Pattern
from Redy.Collections.Traversal import chunk_by
from Redy.Magic.Classic import cast
from Redy.Tools.PathLib import Path
from ..Optimize import optimize
from .rbnf_parser import Statements, bootstrap, rbnf_lexing, IfNotNone
from .common import *
import os

C = Literal.C
N = Literal.N
NC = Literal.NC
V = Literal.V
R = Literal.R


class Mapping1(Mapping):
    __slots__ = ['mapping', 'tokens', 'state', 'globals']

    def __len__(self) -> int:
        return len(self.mapping)

    def __iter__(self):
        yield from self.mapping

    def __init__(self, tokens: Sequence[Tokenizer], state: State, globals: dict):
        self.mapping = state.ctx
        self.tokens = tokens
        self.state = state
        self.globals = globals

    def __getitem__(self, k):
        v = {
            'state': lambda: self.state, 'tokens': lambda: self.tokens
        }.get(k, lambda: self.mapping.get(k))()

        return v if v is not None else self.globals.get(k)

    def __setitem__(self, key, value):
        self.mapping[key] = value


class Mapping2(Mapping):
    __slots__ = ['mapping', 'state', 'globals']

    def __len__(self) -> int:
        return len(self.mapping)

    def __iter__(self):
        yield from self.mapping

    def __init__(self, state: State, globals: dict):
        self.mapping = state.ctx
        self.state = state
        self.globals = globals

    def __getitem__(self, k):
        if k == 'state':
            return self.state
        v = self.mapping.get(k)
        if v is None:
            return self.globals.get(k)
        return v

    def __setitem__(self, key, value):
        self.mapping[key] = value


def create_ctx():
    import builtins
    return dict(prefix={}, lexer_table=[], cast_map={}, _lexer_table=dict(regex=set(), literal=set()), lang={},
                namespace={}, ignore_lexer_names=set(), **builtins.__dict__)


def parse(codes: str) -> StmtsASDL:
    state = State(bootstrap)
    tokens = tuple(rbnf_lexing(codes))
    result = Statements.match(tokens, state)
    if result.status is Unmatched:
        raise ValueError(state.max_fetched)
    return result.value


@Pattern
def visit(asdl: ASDL, ctx: dict):
    return type(asdl)


@visit.case(NameASDL)
def visit(a: NameASDL, ctx: dict) -> Union[Atom.Named, Literal.N]:
    if a.value == '_':
        return Atom.Any
    return ctx['namespace'][a.value]


@visit.case(NameBindASDL)
def visit(a: NameBindASDL, ctx: dict) -> Atom.Bind:
    return visit(a.body, ctx) @ a.name


@visit.case(StrASDL)
def visit(a: StrASDL, ctx) -> Literal.C:
    if a.value.startswith('\''):
        value = a.value[1:-1]
        ret = C(value)
    else:
        prefix = a.value[0]
        value = a.value[2:-1]

        res = {
            'R': lambda: R(value), 'C': lambda: C(value), 'V': lambda: V(value), 'N': lambda: N(value),
        }.get(prefix, None)

        if res:
            ret = res()
        else:
            name = ctx['prefix'].get(prefix)
            ret = NC(name, value)

    _lexer_table = ctx['_lexer_table']
    if ret[0] is C and value not in _lexer_table['literal']:
        _lexer_table['literal'].add(value)
        ctx['lexer_table'].append(('auto_const' | ToConst, str_lexer(value)))

    return ret


@visit.case(OrASDL)
@cast(optimize)
def visit(a: OrASDL, ctx: dict) -> Composed.Or:
    return Composed.Or([visit(each, ctx) for each in a.value])


@visit.case(AndASDL)
@cast(optimize)
def visit(a: AndASDL, ctx: dict):
    return Composed.And([visit(each, ctx) for each in a.value])


@visit.case(RepeatASDL)
def visit(a: RepeatASDL, ctx: dict):
    return visit(a.body, ctx)(a.least, a.most)


@visit.case(ReverseASDL)
def visit(a: ReverseASDL, ctx: dict):
    return ~visit(a.value, ctx)


@visit.case(ImportASDL)
def visit(a: ImportASDL, ctx: dict):
    if a.is_python_import:
        from_ = '.'.join(a.paths)
        import_items = '*' if not a.import_items else ', '.join(a.import_items)
        new_ctx = {}
        exec(f'from {from_} import {import_items}', new_ctx)
        if import_items is '*':
            ctx.update(new_ctx)
        else:
            for each in a.import_items:
                ctx[each] = new_ctx[each]
        return

    paths = [Path(os.environ.get('RBNF_HOME', './'))]
    for each_into in a.paths:
        new_path = []
        for each_path in paths.copy():
            if each_into == '*':
                new_path.extend(each_path.list_dir())
            else:
                new_path.append(each_path.into(each_into))
        paths = new_path
    if not a.import_items:
        for path in paths:
            with path.open('r') as f:
                text = f.read()
            asdl = parse(text)
            yield from (visit(each, ctx) for each in asdl.value if
                        hasattr(each, 'name') and each.name in a.import_items)

    elif len(paths) > 1:
        raise ValueError("Cannot wildly import specific symbol.(import *.* [some])")
    else:
        path = paths[0]
        with path.open('r') as f:
            text = f.read()
        for end in a.import_items:
            if end in ctx:
                raise ValueError(f"Duplicated symbol `{end}` in both current file and {path}.")
        asdls = parse(text).value
        ends = set(a.import_items)
        to_visits = []
        for each in asdls:
            if hasattr(each, 'name') and each.name in ends:
                to_visits.append(each)
                # visit(each, ctx)
                ends.remove(each.name)
        if any(ends):
            names = ', '.join(ends)
            raise NameError(f"Cannot found name(s) `{names}` at {path}.")

        yield from (visit(each, ctx) for each in to_visits)


def str_asdls_to_lexers(s: List[StrASDL], ctx: dict):
    cache = []
    _lexer_table = ctx['_lexer_table']
    for each in s:
        if each.value.startswith('\''):
            value = each.value[1:-1]
            cache.append(('C', value))
            _lexer_table['literal'].add(value)
        else:
            value = each.value[2:-1]
            prefix = each.value[0]
            assert prefix in ('R', 'C')
            if prefix == 'R':
                _lexer_table['regex'].add(value)
            elif prefix == 'C':
                _lexer_table['literal'].add(value)
            cache.append((prefix, value))

    return map(lambda _: {
        'R': regex_lexer, 'C': lambda arg: str_lexer(sorted(arg, reverse=True) if isinstance(arg, tuple) else arg)
    }[_[0][0]](_[0][1] if len(_) is 1 else tuple(e[1] for e in _)),

               chunk_by(lambda x: x[0])(cache))


@visit.case(LexerASDL)
def visit(a: LexerASDL, ctx: dict):
    name = a.name | ToConst
    if a.alias:
        ctx['prefix'][a.alias] = name

    yield name, N(a.name)

    lexer_table: StrLexerTable = ctx['lexer_table']
    lexer_table.extend(zip(itertools.repeat(name), str_asdls_to_lexers(a.items, ctx)))

    if a.is_const_cast:
        cast_map: CastMap = ctx['cast_map']
        for each in a.items:
            if each.value.startswith('\''):
                cast_map[each.value[1:-1]] = name


def var_hook(codes: str):
    n = codes.rfind('\n')
    if n is -1:
        return f'__result__ = {codes}'
    return f'{codes[:n]}\n__result__ = {codes[n+1:]}'


@visit.case(ParserASDL)
def visit(a: ParserASDL, ctx: dict):
    name = a.name
    lang = ctx['lang']
    if name in ctx['lang']:
        raise NameError(f"duplicated definition of `{name}`")

    when = a.when | IfNotNone(var_hook)
    if when:
        when_code = compile(when, ctx.get('__filename__', '<input>'), 'exec')

        def when_func(tokens, state):
            ctx_view = Mapping1(tokens, state, ctx)
            exec(when_code, ctx, ctx_view)
            return ctx_view['__result__']
    else:
        when_func = None

    with_ = a.with_ | IfNotNone(var_hook)
    if with_:
        with_code = compile(with_, ctx.get('__filename__', '<input>'), 'exec')

        def with_func(tokens, state):
            ctx_view = Mapping1(tokens, state, ctx)
            exec(with_code, ctx, ctx_view)
            return ctx_view['__result__']


    else:
        with_func = None

    rewrite = a.rewrite | IfNotNone(var_hook)
    if rewrite:
        rewrite_code = compile(rewrite, ctx.get('__filename__', '<input>'), 'exec')

        def rewrite_func(state):
            ctx_view = Mapping2(state, ctx)
            exec(rewrite_code, ctx, ctx_view)
            return ctx_view['__result__']

    else:
        rewrite_func = None

    named = PAtom.Named(name, when_func, with_func, rewrite_func)

    yield name, named

    ctx[name] = named
    or_ = visit(a.or_, ctx)
    lang[named[1]] = or_


@visit.case(StmtsASDL)
def visit(a: StmtsASDL, ctx: dict):
    async_objs = []

    for each in a.value:
        it = visit(each, ctx)
        if isinstance(each, IgnoreASDL):
            continue

        if isinstance(each, ImportASDL):
            try:
                async_objs.extend(it)
            except StopIteration:
                pass
        else:
            async_objs.append(it)

    for each in async_objs:
        name, parser = each.send(None)
        ctx['namespace'][name] = parser

    for each in async_objs:
        try:
            each.send(None)
        except StopIteration:
            pass

    lexer_table = ctx['lexer_table']
    cast_map = ctx['cast_map']

    ignore_lexer_names: Set[id] = set(map(lambda it: id(it | ToConst), ctx['ignore_lexer_names']))

    def _lex(codes: str):
        return lexing(codes, lexer_table, cast_map)

    if ignore_lexer_names:
        def lex(codes: str):
            yield from (e for e in _lex(codes) if id(e.name) not in ignore_lexer_names)
    else:
        lex = _lex
    ctx['lex'] = lex


@visit.case(IgnoreASDL)
def visit(a: IgnoreASDL, ctx: dict):
    ctx['ignore_lexer_names'].update(a.names)
