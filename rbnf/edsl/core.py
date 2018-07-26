from .rbnf_analyze import *
from rbnf.core import ParserC
from rbnf.core.ParserC import Tokenizer, State, Literal, ConstStrPool
from rbnf.err import LanguageBuiltError
from rbnf.AutoLexer import lexing
from rbnf._py_tools.unparse import Unparser
from collections import OrderedDict

from Redy.Opt import Macro, feature, constexpr, const
from Redy.Opt import get_ast

exec("from linq import Flow as seq")
from typing import Sequence
import abc
import ast
import typing
import types
import textwrap
import builtins
import io

_internal_macro = Macro()
staging = (const, constexpr)


class _AutoContext:
    def __init__(self, fn):
        self.fn = fn


class FnCodeStr(typing.NamedTuple):
    code: str
    lineno: int
    colno: int
    filename: str
    namespace: dict

    fn_name = None
    fn_args = "tokens", "state"


def unparse(ast: ast.AST):
    if not ast:
        return ""

    with io.StringIO() as ios:
        Unparser(ast, ios)
        return ios.getvalue()


def auto_context(fn):
    return _AutoContext(fn)


def process(fn, bound_names):
    """
    process automatic context variable capturing.
    return the transformed function and its ast.
    """
    if isinstance(fn, _AutoContext):
        fn = fn.fn

    if not bound_names:
        return fn, get_ast(fn.__code__)

    if isinstance(fn, FnCodeStr):
        assign_code_str = "ctx = state.ctx\n" + "\n".join("{0} = ctx.get({0!r})".format(name) for name in bound_names)
        code = "def {0}({1}):\n{2}".format(fn.fn_name, ", ".join(fn.fn_args),
                                           textwrap.indent(f'{assign_code_str}\n{fn.code}', " " * 4))
        module_ast = ast.parse(code, fn.filename)
        module_ast = ast.increment_lineno(module_ast, fn.lineno)
        filename = fn.filename
        name = fn.fn_name
        __defaults__ = None
        __closure__ = None
        __globals__ = fn.namespace

    else:
        code = fn.__code__
        assigns = ast.parse(
            "ctx = state.ctx\n" + "\n".join("{0} = ctx.get({0!r})".format(name) for name in bound_names))
        module_ast = get_ast(fn.__code__)
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
        each for each in code_object.co_consts if isinstance(each, types.CodeType) and each.co_name == name)
    # noinspection PyArgumentList,PyUnboundLocalVariable
    ret = types.FunctionType(code_object, __globals__, name, __defaults__, __closure__)
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
        self.named_parsers = OrderedDict()
        self.dump_spec = OrderedDict()

        self.implementation = {}
        self.lexer = None
        self.ignore_lst = {}
        self.prefix = {}

        self.lexer_makers: typing.List[Lexer] = []
        self.lazy_def_parsers: typing.List[Parser] = []

        # in rewrite/when/with clause, the global scope is exactly `Language.namespace`.
        self.namespace = {**builtins.__dict__}

        self._lexer_factors = []
        self._is_built = False

    def _kind(self, name):
        named_parser = self.named_parsers[name]
        if isinstance(named_parser, ParserC.Atom):
            return "ruiko.Parser"
        elif isinstance(named_parser, ParserC.Literal):
            return "ruiko.Lexer"

    def dumps(self):
        static_method_prefix = '@staticmethod' + '\n'
        line_join = '\n'.join

        code = line_join("\n"
                         f"@{self.lang_name}\n"
                         f"class {name}({self._kind(name)}):\n"
                         f"{textwrap.indent(line_join(map(static_method_prefix.__add__ , spec_fn)), ' ' * 4)}\n"
                         "" for name, spec_fn in self.dump_spec.items())
        return (f"# File automatically generated by RBNF.\n"
                f"from rbnf.bootstrap import loader as ruiko\n"
                f"{self.lang_name} = ruiko.Language({self.lang_name!r})\n"
                f"{code}"
                f"{self.lang_name}.ignore({repr(list(self.ignore_lst.values()))[1:-1]})\n"
                f"{self.lang_name}.build()\n")

    def __call__(self, cls):
        cls.lang = self
        if issubclass(cls, Parser):
            self.lazy_def_parsers.append(cls)
            ret = ParserC.Atom.Named(cls.__name__)

        elif issubclass(cls, Lexer):
            self.lexer_makers.append(cls)
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
            raise LanguageBuiltError(f"Language {self.lang_name} is already built!")

        def _process(fn, binding_names):
            if hasattr(fn, '__isabstractmethod__') and fn.__isabstractmethod__:
                return None, None
            if isinstance(fn, classmethod):
                # noinspection PyTypeChecker
                fn_, ast = _process(fn.__func__, binding_names)
                return classmethod(fn_), ast

            if isinstance(fn, types.MethodType):
                # noinspection PyTypeChecker
                fn_, ast = _process(fn.__func__, binding_names)
                return types.MethodType(fn_, fn.__self__), ast

            return process(fn, binding_names)

        def _get_ast(fn):
            if hasattr(fn, '__isabstractmethod__') and fn.__isabstractmethod__:
                return None
            if isinstance(fn, classmethod):
                # noinspection PyTypeChecker
                return _get_ast(fn.__func__)
            if isinstance(fn, types.MethodType):
                # noinspection PyTypeChecker
                return _get_ast(fn.__func__)
            return get_ast(fn.__code__)

        lexer_factors = self._lexer_factors
        cast_map = {}
        dump_spec = self.dump_spec
        prefix_map = self.prefix

        def lexer_spec_maker():
            if regex:
                yield f"def regex(): return {regex!r}"

            if constants:
                yield f"def constants(): return {constants!r}"

            if prefix:
                yield f"def constants(): return {prefix!r}"

            if cast:
                yield f"def cast(): return {cast!r}"

        for cls in self.lexer_makers:
            regex = cls.regex()
            if regex:
                if isinstance(regex, str):
                    regex = [regex]
                lexer_factors.append(RegexLexerFactor(cls.__name__, regex))

            constants = cls.constants()
            if constants:
                if isinstance(constants, str):
                    constants = [constants]
                lexer_factors.append(ConstantLexerFactor(cls.__name__, constants))

            cast = cls.cast()
            if cast:
                name = ConstStrPool.cast_to_const(cls.__name__)
                cast_map.update({constant: name for constant in constants})

            prefix = cls.prefix()
            if prefix:
                prefix_map[prefix] = ConstStrPool.cast_to_const(cls.__name__)

            dump_spec[cls.__name__] = list(lexer_spec_maker())

        lang = self.implementation

        def parser_spec_maker():
            if when_ast:
                yield unparse(when_ast)
            if fail_if_ast:
                yield unparse(fail_if_ast)
            if rewrite_ast:
                yield unparse(rewrite_ast)

        for cls in self.lazy_def_parsers:
            implementation: ParserC.Parser = cls.bnf()
            lexer_factors.extend(get_lexer_factors(implementation))
            binding_names = get_binding_names(implementation)

            when, when_ast = _process(cls.when, ())
            fail_if, fail_if_ast = _process(cls.fail_if, binding_names)
            rewrite, rewrite_ast = _process(cls.rewrite, binding_names)

            lang[cls.__name__] = implementation, when, fail_if, rewrite

            # @formatter:off
            dump_spec[cls.__name__] = [f"def bnf():\n  return {dumps(implementation)}", *parser_spec_maker()]
            # @formatter:on

        def f1(e: LexerFactor):
            return e.name, type(e)

        def f2(e: typing.Tuple[typing.Tuple[str, type], typing.List[LexerFactor]]):
            (name, ty), members = e

            def stream():
                for each in members:
                    yield from each.factors

            factors = set(stream())

            if ty is ConstantLexerFactor:
                # avoid to cover sub-patterns.
                factors = sorted(factors, reverse=True)
            else:
                factors = tuple(factors)
            return ty(name, factors)

        # @formatter:off
        # noinspection PyProtectedMember
        lexer_table = (seq(
                        lexer_factors).chunk_by(f1)
                                      .map(f2)
                                      .map(lambda it: it.to_lexer())
                                      .to_list()
                                      ._)
        # @formatter:on

        @feature(staging)
        def filter_token(tk: Tokenizer):
            return constexpr[id](tk.name) not in constexpr[self.ignore_lst]

        @feature(staging)
        def lexer(text: str):
            ignore_lst: const = self.ignore_lst
            cm: const = cast_map

            result = constexpr[lexing](text, constexpr[lexer_table], cm if constexpr[cm] else None)
            if constexpr[ignore_lst]:
                return filter(constexpr[filter_token], result)
            else:
                return result

        self.lexer = lexer
        self._is_built = True
