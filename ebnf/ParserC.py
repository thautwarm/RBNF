from Redy.ADT import traits
from Redy.ADT.Core import RDT

from .AST import *
from .Result import *
from .State import *
from ._literal_matcher import *
from Redy.Magic.Pattern import Pattern
from warnings import warn

Context = dict
LRFunc = Callable[[AST, Context], Result]
When = Callable[[Sequence[Tokenizer], State], bool]
With = Callable[[Sequence[Tokenizer], State, Context], bool]
Rewrite = Callable[[State, Context], Named]


class Parser:

    def match(self, tokenizers: Sequence[Tokenizer], state: State, context: Context) -> Result:
        raise NotImplemented

    def __call__(self, least, most=-1) -> 'Parser':
        return Composed.Seq(self, least, most)

    def __invert__(self):
        return Composed.AnyNot(self)

    def __matmul__(self, other: str):
        return Atom.Bind(other, self)

    def __or__(self, other):
        if self[0] is Composed.Or:
            if other[0] is Composed.Or:
                return Composed.Or([*self[1], *other[1]])
            return Composed.Or([*self[1], other])
        elif other[0] is Composed.Or:
            return Composed.Or([self, *other[1]])
        return Composed.Or([self, other])

    def __add__(self, other):
        if self[0] is Composed.And:
            if other[0] is Composed.And:
                return Composed.And([*self[1], *other[1]])
            return Composed.And([*self[1], other])
        elif other[0] is Composed.And:
            return Composed.And([self, *other[1]])
        return Composed.And([self, other])


@singleton
class Any(Parser):

    def match(self, tokenizers: Sequence[Tokenizer], state: State, context: Context) -> Result:
        try:
            token = tokenizers[state.counted]
        except IndexError:
            return unmatch
        state.new_one()
        return Result(Matched, token)


@data
class Literal(Parser, traits.ConsInd, traits.Dense, traits.Im):
    # match by regex
    # indeed it's stupid to use regex matching when parsing, however EBNFParser supplies everything.
    R: RDT[lambda regex: [[make_regex_matcher(regex)], f'R{regex.__repr__()}']]

    # match by runtime string(equals)
    V: RDT[lambda runtime_str: [[make_runtime_str_matcher(runtime_str)], f'R{runtime_str.__repr__()}']]

    # match by name -> const string
    N: RDT[lambda name: [[make_name_matcher(name)], f'N{name.__repr__()}']]

    C: RDT[lambda const_string: [[make_const_str_matcher(const_string)], f'C{const_string.__repr__()}']]

    NC: RDT[lambda name, const_string: [[make_name_and_const_str_matcher(name, const_string)],
                                        f'<{name}>{const_string.__repr__()}']]

    Invert: RDT[lambda literal: [[lambda token: not literal[1](token)], f'~{literal}']]

    def __str__(self):
        return str(self.__inst_str__)

    def match(self, tokenizers: Sequence[Tokenizer], state: State, context: Context) -> Result:
        try:
            token = tokenizers[state.counted]
        except IndexError:
            return unmatch
        if self[1](token):
            state.new_one()
            return Result(Matched, token)
        return unmatch

    def __invert__(self):
        # noinspection PyCallingNonCallable
        return Literal.Invert(self)


@data
class Atom(Parser, traits.ConsInd, traits.Dense, traits.Im):
    Bind: lambda name, or_parser: f'({or_parser}) as {name}'
    Named: RDT[
        lambda ref_name, when, with_, rewrite: [[ConstStrPool.cast_to_const(ref_name), when, with_, rewrite], ref_name]]

    @Pattern
    def match(self, tokenizers: Sequence[Tokenizer], state: State, context: Context) -> Result:
        return self[0]


@Atom.match.case(Atom.Bind)
def _bind_match(self: Atom, tokenizers: Sequence[Tokenizer], state: State, context: Context):
    _, name, parser = self
    result = parser.match(tokenizers, state, context)

    if result.status is FindLR:
        stacked_func: LRFunc = result.value

        def stacked_func_(ast: AST, context_: Context):
            stacked_result = stacked_func(ast, context_)
            if stacked_result.status is Matched:
                context_[name] = stacked_result.value
            return stacked_result

        result.value = stacked_func_
    elif result.status is Matched:
        context[name] = result.value

    return result


@Atom.match.case(Atom.Named)
def _named_match(self: Atom, tokenizers: Sequence[Tokenizer], state: State, context: Context):
    context = {}
    _, name, when, with_, rewrite = self
    lang = state.lang
    when: When
    with_: With
    rewrite: Rewrite

    if when and not when(tokenizers, state):
        return unmatch

    parser: 'Composed.Or' = lang[name]
    assert parser[0] in (Composed.Or, Composed.And)

    if name in state:
        if state.lr_name:
            return unmatch

        state.lr_name = name

        def stacked_func(ast: AST, _: Context):
            return Result(Matched, ast)

        return Result(FindLR, stacked_func)

    state.append(name)

    result: Result = parser.match(tokenizers, state, context)

    if result.status is Unmatched:
        return unmatch
    elif result.status is Matched:
        if with_ and not with_(tokenizers, state, context):
            return unmatch
        return Result(Matched, Named(name, rewrite(state, context) if rewrite else result.value))
    elif result.status is FindLR:
        stacked_func: LRFunc = result.value

        if state.lr_name is not name:
            def stacked_func_(ast: AST, context_: Context):
                stacked_result = stacked_func(ast, context_)
                if stacked_result.status is Matched:
                    stacked_result.value = Named(name, rewrite(state, context_) if rewrite else stacked_result.value)

                return stacked_result

            result.value = stacked_func_
            return result

        with state.do_left_recursion():
            result: Result = parser.match(tokenizers, state, context)
            if result.status is Unmatched:
                return result

            assert result.status is not FindLR

            if with_ and not with_(tokenizers, state, context):
                return unmatch

            # noinspection PyTypeChecker
            head: Named = Named(name, rewrite(state, context) if rewrite else result.value)
            # stack jumping
            while True:
                ctx = context.copy()
                res = stacked_func(head, ctx)
                history = state.commit()
                if res.status is Unmatched:
                    state.reset(history)
                    break
                assert res.status is Matched
                # noinspection PyTypeChecker
                head = Named(name, rewrite(state, ctx) if rewrite else res.value)
            result.value = head
            return result

    return result


@data
class Composed(Parser, traits.ConsInd, traits.Dense, traits.Im):
    And: lambda atoms: " ".join(map(str, atoms))
    Or: lambda ands: " | ".join(map(str, ands))
    Seq: lambda parser, least, most: f'{parser}({least} {most})'
    AnyNot: lambda which: f'not {which}'

    def __str__(self):
        return self.__inst_str__

    @Pattern
    def match(self, tokenizers: Sequence[Tokenizer], state: State, context: Context) -> Result:
        return self[0]


@Composed.match.case(Composed.AnyNot)
def _not_match(self: Composed, tokenizers: Sequence[Tokenizer], state: State, context: Context) -> Result:
    which = self[1]
    history = state.commit()
    if which.match(tokenizers, state, context).status is Unmatched:
        state.reset(history)
        return Any.match(tokenizers, state, context)
    state.reset(history)
    return unmatch


@Composed.match.case(Composed.And)
def _and_match(self: Composed, tokenizers: Sequence[Tokenizer], state: State, context: Context) -> Result:
    atoms: List[Atom] = self[1]
    history = state.commit()
    nested = Nested()

    # no tco here, so I have to repeat myself.
    for i in range(len(atoms)):
        atom = atoms[i]

        each_result = atom.match(tokenizers, state, context)


        if each_result.status is Unmatched:
            state.reset(history)
            return unmatch
        elif each_result.status is Matched:
            each_value = each_result.value
            if isinstance(each_value, Nested):
                nested.extend(each_value)
            else:
                nested.append(each_value)
            continue
        else:
            stacked_func: LRFunc = each_result.value

            def stacked_func_(ast: AST, context_: Context):
                stacked_result = stacked_func(ast, context_)
                if stacked_result.status is Matched:
                    stacked_nested = nested.copy()
                    for j in range(i + 1, len(atoms)):
                        atom_ = atoms[j]
                        each_result_ = atom_.match(tokenizers, state, context)
                        if each_result_.status is Matched:
                            each_value_ = each_result_.value
                            if isinstance(each_value_, Nested):
                                stacked_nested.extend(each_value_)
                            else:
                                stacked_nested.append(each_value_)
                            continue
                        return unmatch
                    stacked_result.value = stacked_nested

                return stacked_result

            each_result.value = stacked_func_
            return each_result

    return Result(Matched, nested)


@Composed.match.case(Composed.Or)
def _or_match(self: Composed, tokenizers: Sequence[Tokenizer], state: State, context: Context) -> Result:
    ors: Sequence[Composed] = self[1]
    for or_ in ors:
        result = or_.match(tokenizers, state, context)
        if result.status is not Unmatched:
            return result
        continue
    return unmatch


@Composed.match.case(Composed.Seq)
def _seq_match(self: Composed, tokenizers: Sequence[Tokenizer], state: State, context: Context) -> Result:
    FINISH = 0
    CONTINUE = 1
    FAIL = 2

    _, parser, least, most = self
    history = state.commit()
    nested = Nested()

    def foreach(times: int, parsed: Nested):
        if times == most:
            return FINISH
        sub_res: Result = parser.match(tokenizers, state, context)
        if sub_res.status is Unmatched:
            if times > least:
                return FINISH
            return FAIL
        elif sub_res.status is FindLR:
            if least is 0:
                warn(f"Left recursion supporting is ambiguous with repeatable parser({self}) that which couldn't fail.")
                return FAIL
            return sub_res.value

        sub_value = sub_res.value
        if isinstance(sub_value, Nested):
            parsed.extend(sub_value)
        else:
            parsed.append(sub_value)
        return CONTINUE

    now = 0
    while True:
        status = foreach(now, nested)
        if status is CONTINUE:
            now += 1
            continue
        elif status is FINISH:
            return Result(Matched, nested)

        elif status is FAIL:
            state.reset(history)
            return unmatch

        stacked_func = status

        def stacked_func_(ast: AST, context_: Context):
            now_ = now
            parsed_ = nested.copy()
            res: Result = stacked_func(ast, context_)

            if res.status is Unmatched:
                return unmatch if now_ < least else Result(Matched, parsed_)

            now_ += 1
            while True:
                status_ = foreach(now_, parsed_)
                if status_ is FINISH:
                    return Result(Matched, parsed_)
                elif status_ is CONTINUE:
                    now_ += 1
                    continue
                return unmatch

        return Result(FindLR, stacked_func_)
