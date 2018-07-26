import operator
from functools import reduce

from rbnf.core.Optimize import optimize
from rbnf.core.ParserC import Literal, Atom as _Atom, State, Tokenizer
from rbnf.core import ParserC
from rbnf.edsl import *
from rbnf.AutoLexer import rbnf_lexer
from rbnf.std.common import recover_codes, Name, Str, Number
from typing import Sequence
import typing
import builtins
from linq import Flow as seq

C = Literal.C
N = Literal.N
NC = Literal.NC

END = N('END')


class ASDL:
    pass


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
    fn_args = "state"
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
            return state.data.named_parsers[name.value]
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
                     | C("as") + C('[') @ "is_seq" + Name@"bind" + C("]")
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
                ctx['name'].append(ret)
                # noinspection PyTypeChecker
                ret = ret >> name
            else:
                ctx['name'] = ret
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
                    (C("[") + Name @ "language" + C("]")).optional
                    + C("import")
                    + Name @ "head"
                    + (C('.') + (C('*') | Name >> "tail")).unlimited
                    +  C('.') + C('[') + (C('*') | Name.unlimited @ "import_items") + C(']'))
        # @formatter:on


"""
    # def rewrite(state: State):
    #     language: Tokenizer
    #     head: Tokenizer
    #     tail: typing.List[Tokenizer]
    #     import_items: typing.List[Tokenizer]
    #     raise NotImplemented

"""


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
    def rewrite(cls, state: State):
        name: Tokenizer
        impl: ParserC.Parser
        when: When.Data
        fail_if: With.Data
        rewrite: With.Data
        lang: Language = state.data

        methods = {}
        if when:
            methods['when'] = when[0]
        if fail_if:
            methods['fail_if'] = fail_if[0]
        if rewrite:
            methods['rewrite'] = rewrite[0]

        methods['bnf'] = lambda: impl
        lang(type(name.value, (Parser,), methods))


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
    def rewrite(cls, state: State):
        name: Tokenizer
        cast: typing.Optional
        new_prefix: Tokenizer
        lexer_factors: typing.List[Tokenizer]
        lang: Language = state.data
        new_prefix = new_prefix

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

        lang(type(name.value, (Lexer,), methods))


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
    def rewrite(cls, state: State):
        return state.data


rbnf.build()
rbnf.lexer = rbnf_lexer.rbnf_lexing
