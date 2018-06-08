from Redy.ADT import traits
from Redy.ADT.Core import RDT, data

from .AST import *
from .Result import *
from .State import *

from ._literal_matcher import *
from Redy.Magic.Pattern import Pattern
from warnings import warn

Context = dict
LRFunc = Callable[[AST], Result]
When = Callable[[Sequence[Tokenizer], State], bool]
With = Callable[[Sequence[Tokenizer], State], bool]
Rewrite = Callable[[State], Named]


class ConsInd(traits.Ind):  # index following constructing
    def __getitem__(self: traits.IData, i):
        # noinspection PyUnresolvedReferences
        return self.__structure__[i] if self.__structure__ else self


class Parser:

    def match(self, tokenizers: Sequence[Tokenizer], state: State) -> Result:
        raise NotImplemented

    def repeat(self, least, most=-1) -> 'Parser':
        return self(least, most)

    @property
    def one_or_more(self):
        return self.repeat(1, -1)

    @property
    def unlimited(self):
        return self.repeat(0)

    @property
    def optional(self):
        return self.repeat(0, 1)

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


@data
class Literal(Parser, ConsInd, traits.Dense, traits.Im):
    # match by regex
    # indeed it's stupid to use regex matching when parsing, however EBNFParser supplies everything.
    R: RDT[lambda regex: [[make_regex_matcher(regex)], f'R{regex.__repr__()}']]

    # match by runtime string(equals)
    V: RDT[lambda runtime_str: [[make_runtime_str_matcher(runtime_str)], f'V{runtime_str.__repr__()}']]

    # match by name -> const string
    N: RDT[lambda name: [[make_name_matcher(name)], f'N{name.__repr__()}']]

    C: RDT[lambda const_string: [[make_const_str_matcher(const_string)], f'{const_string.__repr__()}']]

    NC: RDT[lambda name, const_string: [[make_name_and_const_str_matcher(name, const_string)],
                                        f'<{name}>{const_string.__repr__()}']]

    Invert: RDT[lambda literal: [[lambda token: not literal[1](token)], f'~{literal}']]

    def __str__(self):
        return str(self.__inst_str__)

    def match(self, tokenizers: Sequence[Tokenizer], state: State) -> Result:
        try:
            token = tokenizers[state.end_index]
        except IndexError:
            return Result.mismatched
        if self[1](token):
            state.new_one()
            return Result.match(token)
        return Result.mismatched

    def __invert__(self):
        # noinspection PyCallingNonCallable
        return Literal.Invert(self)


@data
class Atom(Parser, ConsInd, traits.Dense, traits.Im):
    Bind: lambda name, or_parser: f'({or_parser}) as {name}'
    Named: RDT[
        lambda ref_name, when, with_, rewrite: [[ConstStrPool.cast_to_const(ref_name), when, with_, rewrite], ref_name]]

    Any: '_'

    @Pattern
    def match(self, tokenizers: Sequence[Tokenizer], state: State) -> Result:
        return self[0] if self.__structure__ else self


@Atom.match.case(Atom.Any)
def _any_match(_, tokenizers: Sequence[Tokenizer], state: State) -> Result:
    try:
        token = tokenizers[state.end_index]
    except IndexError:
        return Result.mismatched
    state.new_one()
    return Result.match(token)


@Atom.match.case(Atom.Bind)
def _bind_match(self: Atom, tokenizers: Sequence[Tokenizer], state: State):
    _, name, parser = self
    result = parser.match(tokenizers, state)

    if result.status is FindLR:
        stacked_func: LRFunc = result.value

        def stacked_func_(ast: AST):
            stacked_result = stacked_func(ast)
            if stacked_result.status is Matched:
                state.ctx = state.ctx.copy()
                state.ctx[name] = stacked_result.value
            return stacked_result

        return Result.find_lr(stacked_func_)

    elif result.status is Matched:
        ctx = state.ctx = state.ctx.copy()
        ctx[name] = result.value

    return result


@Atom.match.case(Atom.Named)
def _named_match(self: Atom, tokenizers: Sequence[Tokenizer], state: State):
    _, name, when, with_, rewrite = self
    lang = state.lang
    if when and not when(tokenizers, state):
        return Result.mismatched

    parser: 'Composed.Or' = lang[name]

    if name in state:
        if state.lr_name:
            return Result.mismatched

        state.lr_name = name

        def stacked_func(ast: AST):
            return Result(Matched, ast)

        return Result.find_lr(stacked_func)

    with state.leave_with_context_recovery():
        state.append(name)
        state.ctx = {}

        result: Result = parser.match(tokenizers, state)
        if result.status is Matched:
            if with_ and not with_(tokenizers, state):
                return Result.mismatched

            return Result(Matched, rewrite(state) if rewrite else Named(name, result.value))

        elif result.status is FindLR:
            stacked_func: LRFunc = result.value

            if state.lr_name is not name:
                def stacked_func_(ast: AST):
                    stacked_result = stacked_func(ast)
                    if stacked_result.status is Matched:
                        return Result.match(rewrite(state) if rewrite else Named(name, stacked_result.value))
                    return stacked_result

                return Result.find_lr(stacked_func_)
        else:
            return Result.mismatched

        # find lr and state.lr_name is name

        with state.left_recursion():
            original_ctx = state.ctx
            state.ctx = original_ctx.copy()

            result: Result = parser.match(tokenizers, state)
            if result.status is Unmatched:
                return result

            # assert result.status is not FindLR

            if with_ and not with_(tokenizers, state):
                return Result.mismatched

            head: Named = rewrite(state) if rewrite else Named(name, result.value)
            # stack jumping
            while True:
                with state.leave_with_context_recovery():
                    state.ctx = state.ctx.copy()
                    res = stacked_func(head)
                if res.status is Unmatched:
                    break

                # assert res.status is Matched
                head = rewrite(state) if rewrite else Named(name, res.value)
            result.value = head
            return result


@data
class Composed(Parser, ConsInd, traits.Dense, traits.Im):
    And: lambda atoms: "({})".format(" ".join(map(str, atoms)))
    Or: lambda ands: "({})".format(" | ".join(map(str, ands)))
    Seq: lambda parser, least, most: f'({parser}){{{least} {most}}}'
    Jump: lambda switch_cases: "{{{}}}".format(
            ', '.join(f"({case.__repr__()} => {parser})" for case, parser in switch_cases.items()))

    AnyNot: lambda which: f'not {which}'

    def __str__(self):
        return self.__inst_str__

    @Pattern
    def match(self, tokenizers: Sequence[Tokenizer], state: State) -> Result:
        return self[0]


@Composed.match.case(Composed.AnyNot)
def _not_match(self: Composed, tokenizers: Sequence[Tokenizer], state: State) -> Result:
    which = self[1]
    history = state.commit()
    if which.match(tokenizers, state).status is Unmatched:
        state.reset(history)
        try:
            token = tokenizers[state.end_index]
        except IndexError:
            return Result.mismatched
        state.new_one()
        return Result.match(token)
    state.reset(history)
    return Result.mismatched


@Composed.match.case(Composed.And)
def _and_match(self: Composed, tokenizers: Sequence[Tokenizer], state: State) -> Result:
    atoms: List[Atom] = self[1]
    history = state.commit()
    nested = Nested()
    nested_extend = nested.extend
    nested_append = nested.append
    # no tco here, so I have to repeat myself.
    for i in range(len(atoms)):
        atom = atoms[i]
        each_result = atom.match(tokenizers, state)
        if each_result.status is Unmatched:
            state.reset(history)
            return Result.mismatched
        elif each_result.status is Matched:
            each_value = each_result.value
            if each_value.__class__ is Nested:
                nested_extend(each_value)
            else:
                nested_append(each_value)
            continue
        else:
            stacked_func: LRFunc = each_result.value

            def stacked_func_(ast: AST):
                stacked_result: Result = stacked_func(ast)
                if stacked_result.status is Matched:
                    stacked_value = stacked_result.value
                    stacked_nested = nested.copy()
                    _append = stacked_nested.append
                    _extend = stacked_nested.extend

                    if stacked_value.__class__ is Nested:
                        _extend(stacked_value)
                    else:
                        _append(stacked_value)

                    for j in range(i + 1, len(atoms)):
                        atom_ = atoms[j]
                        each_result_ = atom_.match(tokenizers, state)

                        if each_result_.status is Matched:
                            each_value_ = each_result_.value
                            if each_value_.__class__ is Nested:
                                _extend(each_value_)
                            else:
                                _append(each_value_)
                            continue
                        return Result.mismatched

                    return Result.match(stacked_nested)
                return stacked_result

            return Result.find_lr(stacked_func_)

    return Result(Matched, nested)


@Composed.match.case(Composed.Or)
def _or_match(self: Composed, tokenizers: Sequence[Tokenizer], state: State) -> Result:
    ors: Sequence[Composed] = self[1]
    history = state.commit()
    for or_ in ors:
        result = or_.match(tokenizers, state)
        if result.status is not Unmatched:
            return result

        state.reset(history)
        continue
    return Result.mismatched


@Composed.match.case(Composed.Seq)
def _seq_match(self: Composed, tokenizers: Sequence[Tokenizer], state: State) -> Result:
    FINISH = 0
    CONTINUE = 1
    FAIL = 2

    _, parser, least, most = self
    history = state.commit()
    nested = Nested()

    def foreach(times: int, _extend_fn, _append_fn):
        if times == most:
            return FINISH
        sub_res: Result = parser.match(tokenizers, state)
        if sub_res.status is Unmatched:
            if times >= least:
                return FINISH
            return FAIL
        elif sub_res.status is FindLR:
            if least is 0:
                warn(f"Left recursion supporting is ambiguous with repeatable parser({self}) that which couldn't fail.")
                return FAIL
            return sub_res.value

        sub_value = sub_res.value
        if sub_value.__class__ is Nested:
            _extend_fn(sub_value)
        else:
            _append_fn(sub_value)
        return CONTINUE

    now = 0
    while True:
        status = foreach(now, nested.extend, nested.append)
        if status is CONTINUE:
            now += 1
            continue
        elif status is FINISH:
            return Result(Matched, nested)

        elif status is FAIL:
            state.reset(history)
            return Result.mismatched

        stacked_func = status

        def stacked_func_(ast: AST):
            now_ = now
            parsed_ = nested.copy()
            res: Result = stacked_func(ast)

            if res.status is Unmatched:
                return Result.mismatched if now_ < least else Result.match(parsed_)

            now_ += 1
            while True:
                status_ = foreach(now_, parsed_.extend, parsed_.append)
                if status_ is FINISH:
                    return Result.match(parsed_)
                elif status_ is CONTINUE:
                    now_ += 1
                    continue
                return Result.mismatched

        return Result.find_lr(stacked_func_)


@Composed.match.case(Composed.Jump)
def _jump_match(self: Composed, tokenizers: Sequence[Tokenizer], state: State) -> Result:
    parser_dict: Dict[str, Parser] = self[1]

    try:
        token = tokenizers[state.end_index]
    except IndexError:
        return Result.mismatched

    parser = parser_dict.get(token.value)
    if not parser:
        return Result.mismatched
    history = state.commit()
    state.new_one()
    result = parser.match(tokenizers, state)
    if result.status is Status.Unmatched:
        state.reset(history)
    return result
