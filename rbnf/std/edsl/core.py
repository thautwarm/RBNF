from .rbnf_analyze import *
from rbnf import ParserC
from rbnf.ParserC import Tokenizer, State, Literal
from rbnf.AutoLexer import lexing
from Redy.Opt import Macro, as_store, feature, constexpr, const
from rbnf._literal_matcher import *
from rbnf.Optimize import optimize
from typing import Sequence
from Redy.Opt import get_ast, new_func_maker
import abc
import ast
import typing
import types
from linq import Flow as seq

_internal_macro = Macro()
staging = (const, constexpr)


def process(fn, bound_names):
    if hasattr(fn, '__isabstractmethod__'):
        return fn

    code = fn.__code__
    assigns = ast.parse("ctx = state.ctx\n" + "\n".join("{0} = ctx.{0}".format(name) for name in bound_names))
    module_ast = get_ast(fn)
    fn_ast: ast.FunctionDef = module_ast.body[0]
    fn_ast.body = assigns.body + fn_ast.body
    code_object = compile(ast.Module([fn_ast]), code.co_filename, "exec")
    code_object = next(
            each for each in code_object.co_consts if isinstance(each, types.CodeType) and each.co_name == code.co_name)

    # noinspection PyArgumentList
    return types.FunctionType(code_object, fn.__globals__, fn.__name__, fn.__defaults__, fn.__closure__)


class Parser(abc.ABC):

    @staticmethod
    @abc.abstractmethod
    def bnf():
        raise NotImplemented

    @staticmethod
    @abc.abstractmethod
    def rewrite(state: State):
        raise NotImplemented

    @staticmethod
    @abc.abstractmethod
    def when(tokens: Sequence[Tokenizer], state: State):
        raise NotImplemented

    @staticmethod
    @abc.abstractmethod
    def fail_if(tokens: Sequence[Tokenizer], state: State):
        raise NotImplemented


class Lexer(abc.ABC):

    @staticmethod
    @abc.abstractmethod
    def regex() -> typing.Sequence[str]:
        return []

    @staticmethod
    @abc.abstractmethod
    def constants() -> typing.Sequence[str]:
        return []

    @staticmethod
    @abc.abstractmethod
    def cast() -> bool:
        return False

    # @staticmethod
    # @abc.abstractmethod
    # def alias() -> bool:
    #     return


LexerFactor = typing.Union[RegexLexerFactor, ConstantLexerFactor]


# noinspection PyUnresolvedReferences
class Language:
    def __init__(self, name):
        self.lang_name = name
        self.namespace = {}
        self.lexer_makers: typing.List[Lexer] = []
        self.lazy_def_parsers: typing.List[Parser] = []
        self.lang_areas = {}
        self.lexer_factors = []

        self.lexer = None

    def __call__(self, cls):
        if issubclass(cls, Parser):
            self.lazy_def_parsers.append(cls)
            ret = ParserC.Atom.Named(cls.__name__)

        elif issubclass(cls, Lexer):
            if cls.regex:
                self.lexer_makers.append(cls)
            ret = Literal.N(cls.__name__)

        else:
            raise TypeError
        self.namespace[cls.__name__] = ret
        return ret

    def build(self):
        def abstract_get(fn):
            if hasattr(fn, '__isabstractmethod__'):
                return None
            return fn

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

        lang = self.lang_areas

        for cls in self.lazy_def_parsers:
            implementation: ParserC.Parser = optimize(cls.bnf())

            lexer_factors.extend(get_lexer_factors(implementation))

            binding_names = get_binding_names(implementation)

            when = abstract_get(cls.when)
            fail_if = abstract_get(process(cls.fail_if, binding_names))
            rewrite = abstract_get(process(cls.rewrite, binding_names))

            lang[cls.__name__] = implementation, when, fail_if, rewrite

        def f1(e: LexerFactor):
            return e.name, type(e)

        def f2(e: typing.Tuple[typing.Tuple[str, type], typing.List[LexerFactor]]):
            (name, ty), members = e

            def stream():
                for each in members:
                    yield from each.factors

            return ty(name, tuple(stream()))

        lexer_table = seq(lexer_factors).chunk_by(f1).map(f2).map(lambda it: it.to_lexer()).to_tuple()._

        @feature(staging)
        def lexer(text: str):
            return constexpr[lexing](text, constexpr[lexer_table], cast_map if constexpr[cast_map] else None)

        self.lexer = lexer
