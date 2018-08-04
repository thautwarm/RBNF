from .rbnf_analyze import *
from rbnf.core import ParserC
from rbnf.core.ParserC import State, Literal, ConstStrPool
from rbnf.core.Tokenizer import Tokenizer
from rbnf.err import LanguageBuildingError
from rbnf.auto_lexer import lexing
from rbnf.py_tools.unparse import Unparser
from collections import OrderedDict
from Redy.Opt import feature, constexpr, const
from Redy.Opt import get_ast
from Redy.Magic.Classic import cast
from typing import Sequence
import abc
import ast
import typing
import types
import textwrap
import builtins
import io
import warnings

try:
    from yapf.yapflib.yapf_api import FormatCode

    def _reformat(text):
        return FormatCode(text)[0]

except ModuleNotFoundError:
    warnings.warn("Install yapf to reformat generated code!", UserWarning, 2)

    def _reformat(ret):
        return ret


exec("from linq import Flow as seq")
staging = (const, constexpr)
__all__ = ['auto_context', 'Parser', 'Lexer', 'Language', '_FnCodeStr']

# the inference of linq-t just got stuck and make pycharm boom...


class _AutoContext:
    def __init__(self, fn):
        self.fn = fn


class _FnCodeStr(typing.NamedTuple):
    code: str
    lineno: int
    colno: int
    filename: str
    namespace: dict

    fn_name = "fn"
    fn_args = "tokens", "state"


def unparse(ast: ast.AST):
    if not ast:
        return ""

    with io.StringIO() as ios:
        Unparser(ast, ios)
        return ios.getvalue()


def auto_context(fn):
    return _AutoContext(fn)


class OrderedDefaultDict(OrderedDict):
    cons: typing.Callable

    def set_factory(self, cons):
        self.cons = cons

    def __missing__(self, key):
        value = self[key] = self.cons()
        return value


class CamlMap(typing.Mapping):
    def __init__(self):
        self._ = []

    def __getitem__(self, item):
        for k, v in reversed(self._):
            if k == item:
                return v
        raise KeyError(item)

    def __setitem__(self, key, value):
        self._.append((key, value))

    def __len__(self):
        return len(self._)

    def __iter__(self):
        for k, _ in self._:
            yield k

    def items(self):
        for each in self._:
            yield each


def process(fn, bound_names):
    """
    process automatic context variable capturing.
    return the transformed function and its ast.
    """
    if isinstance(fn, _AutoContext):
        fn = fn.fn

    # noinspection PyArgumentList,PyArgumentList
    if isinstance(fn, _FnCodeStr):

        assign_code_str = '{syms} = map(state.ctx.get, {names})'.format(
            syms=', '.join(bound_names) + ',', names=repr(bound_names))

        code = "def {0}({1}):\n{2}".format(
            fn.fn_name, ", ".join(fn.fn_args),
            textwrap.indent(assign_code_str + '\n' + fn.code, "    "))

        module_ast = ast.parse(code, fn.filename)

        bound_name_line_inc = int(bool(bound_names)) + 1

        module_ast: ast.Module = ast.increment_lineno(
            module_ast, fn.lineno - bound_name_line_inc)

        fn_ast = module_ast.body[0]

        if isinstance(fn_ast.body[-1], ast.Expr):
            # auto addition of tail expr return
            # in rbnf you don't need to write return if the last statement in the end is an expression.
            it: ast.Expr = fn_ast.body[-1]

            fn_ast.body[-1] = ast.Return(
                lineno=it.lineno, col_offset=it.col_offset, value=it.value)

        filename = fn.filename
        name = fn.fn_name

        code_object = compile(module_ast, filename, "exec")

        local = {}
        # TODO: using types.MethodType here to create the function object leads to various problems.
        # Actually I don't really known why util now.
        exec(code_object, fn.namespace, local)
        ret = local[name]

    else:
        if not bound_names:
            return fn, get_ast(fn)

        code = fn.__code__
        assigns = ast.parse("ctx = state.ctx\n" + "\n".join(
            "{0} = ctx.get({0!r})".format(name) for name in bound_names))

        module_ast = get_ast(fn)
        fn_ast: ast.FunctionDef = module_ast.body[0]
        fn_ast.body = assigns.body + fn_ast.body
        module_ast = ast.Module([fn_ast])

        filename = code.co_filename
        name = code.co_name
        __defaults__ = fn.__defaults__
        __closure__ = fn.__closure__
        __globals__ = fn.__globals__

        code_object = compile(module_ast, filename, "exec")

        code_object = next(
            each for each in code_object.co_consts
            if isinstance(each, types.CodeType) and each.co_name == name)

        # noinspection PyArgumentList,PyUnboundLocalVariable
        ret = types.FunctionType(code_object, __globals__, name, __defaults__,
                                 __closure__)
    return ret, module_ast


class Parser(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def bnf(cls):
        raise NotImplemented

    @classmethod
    @abc.abstractmethod
    def rewrite(cls, state: State):
        raise NotImplemented

    @classmethod
    @abc.abstractmethod
    def when(cls, tokens: Sequence[Tokenizer], state: State):
        raise NotImplemented

    @classmethod
    @abc.abstractmethod
    def fail_if(cls, tokens: Sequence[Tokenizer], state: State):
        raise NotImplemented


class Lexer(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def regex(cls) -> typing.Sequence[str]:
        return []

    @classmethod
    @abc.abstractmethod
    def constants(cls) -> typing.Sequence[str]:
        return []

    @classmethod
    @abc.abstractmethod
    def cast(cls) -> bool:
        return False

    @classmethod
    @abc.abstractmethod
    def prefix(cls) -> typing.Optional[str]:
        return None


LexerFactor = typing.Union[RegexLexerFactor, ConstantLexerFactor]


# noinspection PyUnresolvedReferences
class Language:
    def __init__(self, name):
        self.lang_name = name
        self.named_parsers = CamlMap()
        self.dump_spec = CamlMap()
        self.implementation = {}
        self.lexer = None
        self.ignore_lst = {}
        self.prefix = {}
        self.lazy_def = []
        # in rewrite/when/with clause, the global scope is exactly `Language.namespace`.
        self.namespace = {**builtins.__dict__}
        self._lexer_factors = []
        self._is_built = False
        self._backend_imported = []

        # for deep optimization
        self.has_compiled = set()

    @property
    def is_build(self):
        return self._is_built

    def _kind(self, name):
        named_parser = self.named_parsers[name]

        if isinstance(named_parser, ParserC.Atom):
            return "ruiko.Parser"

        elif isinstance(named_parser, ParserC.Literal):
            return "ruiko.Lexer"

        raise TypeError

    def as_fixed(self):

        lang = self.implementation
        lang['.has_compiled'] = self.has_compiled

        for each, *_ in tuple(lang.values()):
            if isinstance(each, ParserC.Parser):
                each.as_fixed(lang)

    def dump(self, filename: str):
        from Redy.Tools.PathLib import Path
        with Path(filename).open('w') as fw:
            fw.write(self.dumps())

    @cast(_reformat)
    def dumps(self):
        static_method_prefix = '@staticmethod' + '\n'
        line_join = '\n'.join

        code = line_join(
            "\n"
            f"@{self.lang_name}\n"
            f"class {name}({self._kind(name)}):\n"
            f"{textwrap.indent(line_join(map(static_method_prefix.__add__ , spec_fn)), ' ' * 4)}\n"
            "" for name, spec_fn in self.dump_spec.items())
        return (
            f"# File automatically generated by RBNF.\n"
            f"{line_join(self._backend_imported)}\n"
            f"from rbnf.bootstrap import loader as ruiko\n"
            f"{self.lang_name} = ruiko.Language({self.lang_name!r})\n"
            f"{code}"
            f"{self.lang_name}.ignore({repr(list(self.ignore_lst.values()))[1:-1]})\n"
            f"{self.lang_name}.build()\n")

    def __call__(self, cls):
        cls.lang = self

        self.lazy_def.append(cls)

        if issubclass(cls, Parser):
            ret = ParserC.Atom.Named(cls.__name__)

        elif issubclass(cls, Lexer):
            ret = Literal.N(cls.__name__)

            prefix = cls.prefix()
            if prefix:
                self.prefix[prefix] = cls.__name__

        else:
            raise TypeError

        self.named_parsers[cls.__name__] = ret
        return ret

    def ignore(self, *ignore_lst: str):
        """
        ignore a set of tokens with specific names
        """

        def stream():
            for each in ignore_lst:
                each = ConstStrPool.cast_to_const(each)
                yield id(each), each

        self.ignore_lst.update(stream())

    # noinspection PyShadowingNames
    def build(self):
        if self._is_built:
            raise LanguageBuildingError(
                f"Language {self.lang_name} is already built!")

        def _process(fn, _binding_names):
            if hasattr(fn, '__isabstractmethod__') and fn.__isabstractmethod__:
                return None, None
            if isinstance(fn, classmethod):
                # noinspection PyTypeChecker
                fn_, ast_ = _process(fn.__func__, _binding_names)
                return classmethod(fn_), ast_

            if isinstance(fn, types.MethodType):
                # noinspection PyTypeChecker
                fn_, ast_ = _process(fn.__func__, _binding_names)
                return types.MethodType(fn_, fn.__self__), ast_

            return process(fn, _binding_names)

        cast_map = {}
        lexer_factors = self._lexer_factors
        dump_spec = self.dump_spec
        prefix_map = self.prefix
        lang = self.implementation

        def lexer_spec_maker():
            if regex:
                yield f"def regex(): return {regex!r}"

            if constants:
                yield f"def constants(): return {constants!r}"

            if prefix:
                yield f"def constants(): return {prefix!r}"

            if cast:
                yield f"def cast(): return {cast!r}"

        def parser_spec_maker():
            if when_ast:
                yield unparse(when_ast)

            if fail_if_ast:
                yield unparse(fail_if_ast)

            if rewrite_ast:
                yield unparse(rewrite_ast)

        for cls in self.lazy_def:
            if issubclass(cls, Lexer):
                regex = cls.regex()
                if regex:
                    if isinstance(regex, str):
                        regex = [regex]
                    lexer_factors.append(RegexLexerFactor(cls.__name__, regex))

                constants = cls.constants()
                if constants:
                    if isinstance(constants, str):
                        constants = [constants]
                    lexer_factors.append(
                        ConstantLexerFactor(cls.__name__, constants))

                cast = cls.cast()
                if cast:
                    name = ConstStrPool.cast_to_const(cls.__name__)
                    cast_map.update({constant: name for constant in constants})

                prefix = cls.prefix()
                if prefix:
                    prefix_map[prefix] = ConstStrPool.cast_to_const(
                        cls.__name__)

                dump_spec[cls.__name__] = list(lexer_spec_maker())

            else:  # Parser

                implementation: ParserC.Parser = cls.bnf()

                lexer_factors.extend(get_lexer_factors(implementation))

                binding_names = tuple(get_binding_names(implementation))

                when, when_ast = _process(cls.when, ())
                fail_if, fail_if_ast = _process(cls.fail_if, binding_names)
                rewrite, rewrite_ast = _process(cls.rewrite, binding_names)

                lang[cls.__name__] = implementation, when, fail_if, rewrite
                dump_spec[cls.__name__] = [
                    f"def bnf():\n  return {dumps(implementation)}",
                    *parser_spec_maker()
                ]

        def name_and_ty(e: LexerFactor):
            return e.name, type(e)

        def merge(e: typing.Tuple[typing.Tuple[str, type], typing.List[
                LexerFactor]]):
            (lexer_group_name, lexer_ty), members = e

            def stream():
                for each in members:
                    yield from each.factors

            factors = set(stream())

            if lexer_ty is ConstantLexerFactor:
                # avoid to cover sub-patterns.
                factors = sorted(factors, reverse=True)

            else:
                factors = tuple(factors)

            return lexer_ty(lexer_group_name, factors)

        # @formatter:off
        # noinspection PyProtectedMember
        lexer_table = (seq(lexer_factors).chunk_by(name_and_ty).map(merge)
                       .map(lambda it: it.to_lexer()).to_list()._)
        # @formatter:on

        @feature(staging)
        def filter_token(tk: Tokenizer):
            return constexpr[id](tk.name) not in constexpr[self.ignore_lst]

        @feature(staging)
        def lexer(text: str):
            ignore_lst: const = self.ignore_lst
            cm: const = cast_map
            result = constexpr[lexing](text, constexpr[lexer_table], cm
                                       if constexpr[cm] else None)
            return filter(constexpr[filter_token],
                          result) if constexpr[ignore_lst] else result

        self.lexer = lexer
        self._is_built = True
