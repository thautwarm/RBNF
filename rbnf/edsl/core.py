from .rbnf_analyze import *
from rbnf import ParserC
from rbnf.ParserC import Tokenizer, State, Literal
from rbnf.AutoLexer import lexing
from Redy.Opt import Macro, feature, constexpr, const
from rbnf._literal_matcher import *
from rbnf.Optimize import optimize
from typing import Sequence
from Redy.Opt import get_ast
from linq import Flow as seq
import abc
import ast
import typing
import types
import textwrap
import builtins

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


def auto_context(fn):
    return _AutoContext(fn)


def process(fn, bound_names):
    if isinstance(fn, _AutoContext):
        fn = fn.fn

    if not bound_names:
        return fn

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
    return types.FunctionType(code_object, __globals__, name, __defaults__, __closure__)


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
        self.named_parsers = {}
        self.namespace = {**builtins.__dict__}
        self.implementation = {}
        self.lexer_makers: typing.List[Lexer] = []
        self.lazy_def_parsers: typing.List[Parser] = []
        self.lexer_factors = []
        self.prefix = {}
        self.lexer = None
        self.ignore_lst = []

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
        self.ignore_lst.extend(map(lambda _: id(ConstStrPool.cast_to_const(_)), ignore_lst))

    def build(self):
        def _process(fn, binding_names):
            if hasattr(fn, '__isabstractmethod__') and fn.__isabstractmethod__:
                return None
            if isinstance(fn, classmethod):
                # noinspection PyTypeChecker
                return classmethod(_process(fn.__func__, binding_names))

            if isinstance(fn, types.MethodType):
                # noinspection PyTypeChecker
                return types.MethodType(_process(fn.__func__, binding_names), fn.__self__)

            return process(fn, binding_names)

        lexer_factors = self.lexer_factors
        cast_map = {}

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

            if cls.cast():
                name = ConstStrPool.cast_to_const(cls.__name__)
                cast_map.update({constant: name for constant in constants})

        lang = self.implementation

        for cls in self.lazy_def_parsers:
            implementation: ParserC.Parser = cls.bnf()
            lexer_factors.extend(get_lexer_factors(implementation))

            binding_names = get_binding_names(implementation)

            cls.when = None if hasattr(cls.when, '__isabstractmethod__') and cls.when.__isabstractmethod__ else cls.when
            cls.fail_if = _process(cls.fail_if, binding_names)
            cls.rewrite = _process(cls.rewrite, binding_names)

            lang[cls.__name__] = [implementation, cls.when, cls.fail_if, cls.rewrite]

        def f1(e: LexerFactor):
            return e.name, type(e)

        def f2(e: typing.Tuple[typing.Tuple[str, type], typing.List[LexerFactor]]):
            (name, ty), members = e

            def stream():
                for each in members:
                    yield from each.factors

            factors = stream()
            if ty is ConstantLexerFactor:
                factors = sorted(factors, reverse=True)
            else:
                factors = tuple(factors)
            return ty(name, factors)

        lexer_table = seq(lexer_factors).chunk_by(f1).map(f2).map(lambda it: it.to_lexer()).to_list()._

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
