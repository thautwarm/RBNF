import itertools
import types

from .rbnf_parser import *
from ..AutoLexer import lexing
from ..ParserC import *
from Redy.Magic.Pattern import Pattern

try:
    from Redy.Opt.ConstExpr import feature
except:
    from Redy.Opt.ConstExpr import optimize as feature
from Redy.Opt.ConstExpr import constexpr, const
from Redy.Collections.Traversal import chunk_by
from Redy.Magic.Classic import cast
from Redy.Tools.PathLib import Path
from ..Optimize import optimize
from .rbnf_parser import Statements, bootstrap, rbnf_lexing, IfNotNone
from .common import *
import os, ast

C = Literal.C
N = Literal.N
NC = Literal.NC
V = Literal.V
R = Literal.R

import ast
import builtins


# class AccessorRewriter(ast.NodeTransformer):
#     def __init__(self, fixed=('tokens', 'state')):
#         super(AccessorRewriter, self).__init__()
#         self.fixed = fixed
#         self.globals = set()

#
# def _init_fn_with_ctx(fn_name, arg_names, stmts):
#     lineno, col_offset = stmts[0].lineno, 0
#
#     if isinstance(stmts[0], ast.Global):
#         stmts[0].names.extend(["tokens", "state"])
#     else:
#         stmts = [ast.Global(lineno=lineno, col_offset=0, names=['tokens', 'state']), *stmts]
#
#     args = [ast.arg(lineno=lineno, col_offset=col_offset, arg=name, annotation=None) for name in arg_names]
#
#     ast.Global(lineno=lineno, col_offset=0, names=['tokens', 'tokens'])
#
#     return ast.Module(body=[ast.FunctionDef(lineno=lineno, col_offset=col_offset, name=fn_name,
#                                             args=ast.arguments(args=args, vararg=None, kwonlyargs=[], kw_defaults=[],
#                                                                kwarg=None, defaults=[]), body=stmts,
#                                             decorator_list=[], returns=None)])


class LocalContextProxy(dict):
    def __len__(self) -> int:
        return len(self.local)

    def __iter__(self):
        yield from self.local

    __slots__ = ['get', 'set', 'glob', 'local']
    undef = object()

    # noinspection PyMissingConstructor
    def __init__(self, global_dict: dict, local_dict: dict):
        self.get = local_dict.get
        self.set = local_dict.__setitem__
        self.local = local_dict
        self.glob = global_dict

    def __getitem__(self, k):
        v = self.get(k, self.undef)

        if v is self.undef:
            return self.glob.get(k)
        return v

    def __setitem__(self, k, v):
        self.set(k, v)


def create_ctx():
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
    *headn, end = a.paths

    if headn:
        for each_into in headn:
            new_paths = []
            action = (lambda new, one: new.extend(one.list_dir())) if each_into == '*' else (
                lambda new, one: new.append(one.into(each_into)))
            for each_path in paths:
                action(new_paths, each_path)
            paths = new_paths

    new_paths = []
    action = (lambda new, one: new.extend(
            [p for p in one.list_dir() if p.relative().lower().endswith(".rbnf")])) if end == '*' else (
        lambda new, one: new.append(one.into(end + '.rbnf')))
    for each_path in paths:
        action(new_paths, each_path)
    paths = new_paths

    if not a.import_items:
        for path in paths:
            with path.open('r') as f:
                text = f.read()
            asdl = parse(text)
            yield from (visit(each, ctx) for each in asdl.value if hasattr(each, 'name'))

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


def var_hook(codes: str) -> Tuple[Optional[ast.Module], ast.Expression]:
    ast_module: ast.Module = ast.parse(codes)
    body = ast_module.body
    if isinstance(body[-1], ast.Expr):
        _expr = body.pop()
        expr = ast.Expression(_expr.value)
    else:
        expr = ast.Expression(ast.NameConstant(lineno=0, col_offset=0, value=None))
    if not body:
        return None, expr
    return ast_module, expr


@visit.case(ParserASDL)
def visit(a: ParserASDL, ctx: dict):
    name = a.name
    lang = ctx['lang']
    if name in ctx['lang']:
        raise NameError(f"duplicated definition of `{name}`")

    when = a.when | IfNotNone(var_hook)
    if when:
        stmts, expr = when
        if stmts is None:
            expr_code = compile(expr, ctx.get('__filename__', f'<{name}-when-clause::return>'), "eval")

            @feature
            def when_func(tokens: Sequence[Tokenizer], state: State):
                inner_ctx = state.ctx
                global_ctx: const = ctx
                inner_ctx.update((('tokens', tokens), ("state", state)))
                local = constexpr[LocalContextProxy](global_ctx, inner_ctx)
                return eval(constexpr[expr_code], global_ctx, local)
        else:
            stmts_code = compile(stmts, ctx.get('__filename__', f'<{name}-when-clause::stmts>'), "exec")
            expr_code = compile(expr, ctx.get('__filename__', f'<{name}-when-clause::return>'), "eval")

            @feature
            def when_func(tokens: Sequence[Tokenizer], state: State):
                inner_ctx = state.ctx
                global_ctx: const = ctx
                inner_ctx.update((('tokens', tokens), ("state", state)))
                local = constexpr[LocalContextProxy](global_ctx, inner_ctx)
                exec(constexpr[stmts_code], global_ctx, local)
                return constexpr[eval](constexpr[expr_code], global_ctx, local)

    else:
        when_func = None

    with_ = a.with_ | IfNotNone(var_hook)
    if with_:
        stmts, expr = with_
        if stmts is None:
            expr_code = compile(expr, ctx.get('__filename__', f'<{name}-with-clause::return>'), "eval")

            @feature
            def with_func(tokens: Sequence[Tokenizer], state: State):
                inner_ctx = state.ctx
                global_ctx: const = ctx
                inner_ctx.update((('tokens', tokens), ("state", state)))
                local = constexpr[LocalContextProxy](global_ctx, inner_ctx)
                return constexpr[eval](constexpr[expr_code], global_ctx, local)

        else:
            stmts_code = compile(stmts, ctx.get('__filename__', f'<{name}-with-clause::stmts>'), "exec")
            expr_code = compile(expr, ctx.get('__filename__', f'<{name}-with-clause::return>'), "eval")

            @feature
            def with_func(tokens: Sequence[Tokenizer], state: State):
                global_ctx: const = ctx
                inner_ctx = state.ctx
                inner_ctx.update((('tokens', tokens), ("state", state)))
                local = constexpr[LocalContextProxy](global_ctx, inner_ctx)
                exec(constexpr[stmts_code], global_ctx, local)
                return constexpr[eval](constexpr[expr_code], global_ctx, local)

    else:
        with_func = None

    rewrite = a.rewrite | IfNotNone(var_hook)
    if rewrite:
        stmts, expr = rewrite
        if stmts is None:
            expr_code = compile(expr, ctx.get('__filename__', f'<{name}-rewrite-clause::return>'), "eval")

            @feature
            def rewrite_func(state: State):
                inner_ctx = state.ctx
                inner_ctx['state'] = state
                global_ctx: const = ctx
                local = constexpr[LocalContextProxy](global_ctx, inner_ctx)
                return constexpr[eval](constexpr[expr_code], local, local)
        else:
            stmts_code = compile(stmts, ctx.get('__filename__', f'<{name}-rewrite-clause::stmts>'), "exec")
            expr_code = compile(expr, ctx.get('__filename__', f'<{name}-rewrite-clause::return>'), "eval")

            @feature
            def rewrite_func(state: State):
                inner_ctx = state.ctx
                inner_ctx['state'] = state
                global_ctx: const = ctx
                local = constexpr[LocalContextProxy](global_ctx, inner_ctx)
                exec(constexpr[stmts_code], local, local)
                return eval(constexpr[expr_code], local, local)
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
