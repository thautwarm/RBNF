import operator
import os
import warnings
from functools import reduce
from rbnf.Color import Red, Green

from rbnf.core.Optimize import optimize
from rbnf.core.ParserC import Literal, Atom as _Atom, State
from rbnf.core.Tokenizer import Tokenizer
from rbnf.core import ParserC
from rbnf.edsl import *
from rbnf.auto_lexer import rbnf_lexer
from rbnf.std.common import recover_codes, Name, Str, Number
from Redy.Tools.PathLib import Path
from typing import Sequence
import typing
import builtins

seq: object
exec("from linq import Flow as seq")

C = Literal.C
N = Literal.N
NC = Literal.NC

END = N('END')


class ASDL:
    pass


PatternName = str


class _Wild:

    def __contains__(self, item):
        return True

    def copy(self):
        return self

    def remove(self, item):
        pass


class MetaState(State):

    def __init__(self, lang_implementation, requires: typing.Union[_Wild, typing.Set[PatternName]], filename=None):
        super(MetaState, self).__init__(lang_implementation, filename)
        self.requires = requires


rbnf = Language("RBNF")


@rbnf
class CodeItem(Parser):
    @classmethod
    def bnf(cls):
        return _Atom.Any

    @classmethod
    def when(cls, tokens: Sequence[Tokenizer], state: State):
        try:
            token = tokens[state.end_index]
        except IndexError:
            return False
        begin_sign: Tokenizer = state.ctx['sign']
        return token.colno > begin_sign.colno


class RewriteCode(FnCodeStr):
    fn_args = "state",
    fn_name = "rewrite"


class WhenCode(FnCodeStr):
    fn_args = "tokens", "state"
    fn_name = "when"


class WithCode(FnCodeStr):
    fn_args = "tokens", "state"
    fn_name = "fail_if"


class Guide(Parser):
    out_cls = FnCodeStr

    @classmethod
    def bnf(cls):
        return optimize(C(cls.__name__.lower()) @ "sign" + CodeItem.one_or_more @ "expr")

    @classmethod
    @auto_context
    def rewrite(cls, state: State):
        ctx = state.ctx
        code_items: ParserC.Nested = ctx['expr']
        first = code_items[0].item
        code = recover_codes(each.item for each in code_items)
        # noinspection PyArgumentList
        return cls.out_cls(code, first.lineno, first.colno, state.filename, state.data.namespace)


@rbnf
class With(Guide):
    out_cls = WithCode
    pass


@rbnf
class When(Guide):
    out_cls = WhenCode
    pass


@rbnf
class Rewrite(Guide):
    out_cls = RewriteCode
    pass


@rbnf
class Primitive(Parser):

    @classmethod
    def bnf(cls):
        # @formatter:off
        return optimize(
                 C('(') + Or @ "or_" + C(')')
               | C('[') + Or @ "optional" + C(']')
               | Name @ "name"
               | Str  @ "str")
        # @formatter:on

    @classmethod
    def rewrite(cls, state: State):
        get = state.ctx.get
        or_: Parser = get('or_')

        optional: Parser = get('optional')

        name: Tokenizer = get('name')

        str: Tokenizer = get('str')

        if name:
            name = name.value
            if name == '_':
                return ParserC.Atom.Any
            return state.data.named_parsers[name]
        if or_:
            return or_
        if optional:
            return optional.optional
        if str:
            value: builtins.str = str.value
            if value.startswith("'"):
                return C(value[1:-1])
            if value[1] is not "'":
                raise TypeError("Prefix could be only sized 1.")
            prefix, value = value[0], value[2:-1]
            try:
                prefix = cls.lang.prefix[prefix]
            except KeyError:
                raise NameError(f"Prefix `{prefix}` not found!")

            return NC(cls.lang.prefix[prefix], value)
        raise TypeError


@rbnf
class Trail(Parser):

    @classmethod
    def bnf(cls):
        # @formatter:off
        return optimize(
                (C('~') @ "rev" + Primitive @ "atom"
                 | Primitive @ "atom"
                    +  ( C('+') @ "one_or_more"
                       | C('*') @ "zero_or_more"
                       | C('{') + Number(1, 2) @ "interval" + C('}')
                       ).optional
                 ) + ( C('as') + Name @ "bind"
                     | C("to") + C('[') @ "is_seq" + Name@"bind" + C("]")
                     ).optional)
        # @formatter:on

    @classmethod
    @auto_context
    def rewrite(cls, state: State):
        rev: object
        atom: ParserC.Parser
        one_or_more: object
        zero_or_more: object
        interval: Sequence[Tokenizer]
        bind: Tokenizer
        is_seq: object
        ctx: dict

        def ret():
            if rev:
                return ~atom
            if one_or_more:
                return atom.one_or_more
            if zero_or_more:
                return atom.unlimited
            if interval:
                if len(interval) is 1:
                    least = int(interval[0].value)
                    most = -1
                else:
                    least, most = map(lambda _: int(_.value), interval)
                return atom.repeat(least, most)
            return atom

        ret: Parser = ret()
        if bind:
            name: str = bind.value
            if is_seq:
                # noinspection PyTypeChecker
                ret = ret >> name
            else:
                ret = ret @ name

        return optimize(ret)


@rbnf
class And(Parser):

    @classmethod
    def bnf(cls):
        return Trail.one_or_more @ "and_seq"

    @classmethod
    @auto_context
    def rewrite(cls, state: State):
        and_seq: ParserC.Nested
        return optimize(reduce(operator.add, and_seq))


@rbnf
class Or(Parser):

    @classmethod
    def bnf(cls):
        return optimize(And @ "head" + (C('|') + (And >> "tail")).unlimited)

    @classmethod
    @auto_context
    def rewrite(cls, state: State):
        tail: ParserC.Nested
        head: ParserC.Parser
        if not tail:
            return head

        return optimize(reduce(operator.or_, tail, head))


@rbnf
class Import(Parser):

    @classmethod
    def bnf(cls):
        # @formatter:off
        return optimize(
                    ((C("[") + Name @ "language" + C("]")).optional
                     + C("import")
                     | C("pyimport") @ "python"
                    )
                    + Name @ "head"
                    + (C('.') + (C('*') | Name >> "tail")).unlimited
                    +  C('.') + C('[') + (C('*') | Name.unlimited @ "import_items") + C(']'))
        # @formatter:on

    @staticmethod
    @auto_context
    def rewrite(state: MetaState):
        language: Tokenizer
        head: Tokenizer
        tail: typing.List[Tokenizer]
        import_items: typing.List[Tokenizer]
        python: Tokenizer
        path_secs = [head.value, *(each.value for each in tail or ())]
        if not import_items:
            requires = _Wild()
        else:
            requires = {each.value for each in import_items}

        if language or python:
            if python:
                warnings.warn("keyword `pyimport` is deprecated, "
                              "use [python] import instead.", DeprecationWarning)
            else:
                language = language.value
                if language != "python":
                    # TODO: c/c++, .net, java
                    raise NotImplementedError(language)

            lang: Language = state.data
            from_item = ".".join(path_secs)
            import_items = "*" if isinstance(requires, _Wild) else "({})".format(', '.join(requires))
            import_stmt = f"from {from_item} import {import_items}"
            lang._backend_imported.append(import_stmt)
            exec(import_stmt, lang.namespace)

        else:
            # TODO: this implementation is wrong but implementing the correct one requires the sperate asts and parsers.
            # See `rbnf.std.compiler`, this one is correct though it's deprecated.

            possible_paths = [Path('./', *path_secs)]
            lang = state.data

            ruiko_home = os.environ.get('RBNF_HOME')

            if ruiko_home:
                possible_paths.append(Path(ruiko_home, *path_secs))

            for path in possible_paths:
                filename = str(path)
                if not filename[:-5].lower().endswith('.rbnf'):
                    filename = filename + '.rbnf'
                    path = Path(filename)
                if not path.exists():
                    continue

                with path.open('r') as file:
                    state = MetaState(rbnf.implementation, requires=requires, filename=str(path))
                    state.data = lang
                    _build_language(file.read(), state=state, filename=path)
                if not requires:
                    break

            if requires and not isinstance(requires, _Wild):
                raise ImportError(requires)


@rbnf
class Ignore(Parser):

    @classmethod
    def bnf(cls):
        return optimize(C("ignore") + C('[') + Name.one_or_more @ "names" + C(']'))

    @classmethod
    @auto_context
    def rewrite(cls, state: State):
        names: typing.List[Tokenizer]
        lang: Language = state.data
        lang.ignore(*(each.value for each in names))


@rbnf
class UParser(Parser):

    @classmethod
    def bnf(cls):
        # @formatter:off
        return optimize(Name @ "name" + C('::=')
                        + C('|').optional
                        + Or @ "impl"
                        + When.optional    @ "when"
                        + With.optional    @ "fail_if"
                        + Rewrite.optional @ "rewrite")
        #  @formatter:on

    @classmethod
    @auto_context
    def rewrite(cls, state: MetaState):
        name: Tokenizer
        impl: ParserC.Parser
        when: When.Data
        fail_if: With.Data
        rewrite: With.Data
        lang: Language = state.data

        requires = state.requires
        name = name.value
        if name not in requires:
            return

        methods = {}
        if when:
            methods['when'] = when[0]
        if fail_if:
            methods['fail_if'] = fail_if[0]
        if rewrite:
            methods['rewrite'] = rewrite[0]

        methods['bnf'] = lambda: impl
        lang(type(name, (Parser,), methods))
        state.requires.remove(name)


@rbnf
class ULexer(Parser):

    @classmethod
    def bnf(cls):
        # @formatter:off
        return optimize(
            Name @ "name" + C('cast').optional @ "cast"
            + (C('as') + Name @ "new_prefix").optional
            +  C(':=')
            +  C('|').optional + Str.one_or_more @ "lexer_factors")
        # @formatter:on

    @classmethod
    @auto_context
    def rewrite(cls, state: MetaState):
        name: Tokenizer
        cast: typing.Optional
        new_prefix: Tokenizer
        lexer_factors: typing.List[Tokenizer]
        lang: Language = state.data
        new_prefix = new_prefix

        requires = state.requires
        name = name.value
        if name not in requires:
            return

        def split_regex_and_constants(tk: Tokenizer):
            v = tk.value
            if v.startswith("R'"):
                return "regex"
            elif v.startswith("'"):
                return "constants"
            raise ValueError(f"Unexpected prefixed string `{v}` at lineno {tk.lineno}, column {tk.colno}.")

        lexer_groups = seq(lexer_factors).group_by(split_regex_and_constants)._
        regex, constants = (lexer_groups[each] for each in ('regex', 'constants'))
        regex = [each[2:-1] for each in seq(regex).map(lambda _: _.value)._]
        constants = [each[1:-1] for each in seq(constants).map(lambda _: _.value)._]

        methods = {'regex': lambda: regex, 'constants': lambda: constants}
        if cast:
            methods['cast'] = lambda: True
        if new_prefix:
            new_prefix = new_prefix.value
            methods['prefix'] = lambda: new_prefix

        lang(type(name, (Lexer,), methods))
        state.requires.remove(name)


@rbnf
class Statement(Parser):

    @classmethod
    def bnf(cls):
        return Import @ "import_" | UParser @ "parser" | ULexer @ "lexer" | Ignore @ 'ignore'


@rbnf
class Grammar(Parser):

    @classmethod
    def bnf(cls):
        return optimize(END.unlimited + (Statement + END.unlimited).unlimited)

    @classmethod
    def rewrite(cls, state: MetaState):
        return state.data


rbnf.build()
rbnf.lexer = rbnf_lexer.rbnf_lexing


def _find_nth(string: str, element, nth: int = 0):
    pos: int = string.index(element)
    while nth:
        pos = string.index(element, pos) + 1
        nth -= 1
    return pos


def _build_language(text: str, state=None, filename=None):
    tokens = tuple(rbnf.lexer(text))
    Grammar.match(tokens, state)

    if not tokens or state.end_index < len(tokens):
        max_fetched = state.max_fetched
        tk: Tokenizer = tokens[max_fetched]
        lineno, colno = tk.lineno, tk.colno
        pos = _find_nth(text, '\n', lineno) + colno - 1
        before = text[max(0, pos - 25): pos]
        later = text[pos: min(pos + 25, len(text))]

        raise SyntaxError(
            "Error at line {}, col {}, see details:\n{}".format(tk.lineno, tk.colno, Green(before) + Red(later)))


def build_language(text, lang: Language, filename):
    state = MetaState(rbnf.implementation, requires=_Wild(), filename=filename)
    state.data = lang
    _build_language(text, state, filename)

    lang.build()
