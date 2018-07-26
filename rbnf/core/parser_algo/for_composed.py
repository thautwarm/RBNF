from ..ParserC import Composed, Atom, Parser, LRFunc
from ..Tokenizer import Tokenizer
from ..State import State
from ..Result import *
from ..AST import *
from Redy.Opt import feature, constexpr, const, goto, label
from typing import Sequence, List
import types
import warnings

staging = (const, constexpr)


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


@Composed.as_fixed.case(Composed.AnyNot)
def as_fixed(self, lang):
    which_ = self[1]
    which_.as_fixed(lang)

    @feature(staging)
    def not_match(tokenizers, state):
        match: const = which_.match
        history = state.commit()
        if match(tokenizers, state).status is constexpr[Unmatched]:
            state.reset(history)
            try:
                token = tokenizers[state.end_index]
            except IndexError:
                return constexpr[Result.mismatched]
            state.new_one()
            return constexpr[Result.match](token)
        state.reset(history)
        return constexpr[Result.mismatched]

    self.match = not_match


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


@Composed.as_fixed.case(Composed.And)
def as_fixed(self, lang):
    atoms_ = self[1]

    for each in atoms_:
        each.as_fixed(lang)

    match_fns_ = [each.match for each in atoms_]

    @feature(staging)
    def and_match(tokenizers, state):
        match_fns: const = match_fns_
        history = state.commit()
        nested = constexpr[Nested]()
        nested_extend = nested.extend
        nested_append = nested.append
        # no tco here, so I have to repeat myself.
        for i in constexpr[range](constexpr[len](match_fns)):
            match = match_fns[i]
            each_result = match(tokenizers, state)
            if each_result.status is constexpr[Unmatched]:
                state.reset(history)
                return constexpr[Result.mismatched]

            elif each_result.status is constexpr[Matched]:
                each_value = each_result.value
                if each_value.__class__ is constexpr[Nested]:
                    nested_extend(each_value)
                else:
                    nested_append(each_value)
                continue
            else:
                stacked_func = each_result.value
                match_fns__ = match_fns

                def stacked_func_(ast):
                    stacked_result = stacked_func(ast)
                    if stacked_result.status is Matched:
                        stacked_value = stacked_result.value
                        stacked_nested = nested.copy()
                        _append = stacked_nested.append
                        _extend = stacked_nested.extend

                        if stacked_value.__class__ is Nested:
                            _extend(stacked_value)
                        else:
                            _append(stacked_value)

                        for j in range(i + 1, len(match_fns__)):
                            match_ = match_fns__[j]
                            each_result_ = match_(tokenizers, state)

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

                return constexpr[Result.find_lr](stacked_func_)

        return constexpr[Result](constexpr[Matched], nested)

    self.match = and_match


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


@Composed.as_fixed.case(Composed.Or)
def as_fixed(self, lang):
    ors_ = self[1]
    for each in ors_:
        each.as_fixed(lang)
    match_fns_ = [each.match for each in ors_]

    @feature(staging)
    def or_match(tokenizers, state):
        match_fns: const = match_fns_
        history = state.commit()
        for match in match_fns:
            result = match(tokenizers, state)

            if result.status is not constexpr[Unmatched]:
                return result

            state.reset(history)
            continue
        x = constexpr[Result.mismatched]
        return x

    self.match = or_match


@Composed.match.case(Composed.Seq)
def _seq_match(self: Composed, tokenizers: Sequence[Tokenizer], state: State) -> Result:
    FINISH = 0
    CONTINUE = 1
    FAIL = 2

    _, parser, least, most = self
    root_history = state.commit()
    nested = Nested()

    def foreach(times: int, _extend_fn, _append_fn):
        if times == most:
            return FINISH
        history = state.commit()
        sub_res: Result = parser.match(tokenizers, state)
        if sub_res.status is Unmatched:
            state.reset(history)
            if times >= least:
                return FINISH
            return FAIL
        elif sub_res.status is FindLR:
            if least is 0:
                state.reset(history)
                warnings.warn(
                    f"Left recursion supporting is ambiguous with repeatable parser({self}) that which couldn't fail.")
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
            if now:
                state.reset(root_history)
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


@Composed.as_fixed.case(Composed.Seq)
def as_fixed(self, lang):
    _, parser_, least_, most_ = self
    parser_.as_fixed(lang)

    @feature(goto, staging)
    def seq_match(tokenizers, state):
        loop: label
        label_finish: label
        label_fail: label
        label_lr: label
        label_return: label

        FINISH: const = 0
        CONTINUE: const = 1
        FAIL: const = 2

        match: const = parser_.match
        least: const = least_
        most: const = most_

        root_history = state.commit()
        nested = constexpr[Nested]()

        now = 0
        _extend_fn = nested.extend
        _append_fn = nested.append

        with loop:
            if constexpr[most >= 0]:
                if now == most:
                    label_finish.jump()

            history = state.commit()
            sub_res = match(tokenizers, state)

            if sub_res.status is constexpr[Unmatched]:
                state.reset(history)

                if now >= least:
                    label_finish.jump()

                label_fail.jump()

            elif sub_res.status is constexpr[FindLR]:
                if constexpr[least is 0]:
                    state.reset(history)

                    warnings.warn(f"Left recursion supporting is ambiguous with "
                                  f"repeatable parser({self}) that which couldn't fail.")

                    label_fail.jump()

                stacked_func = sub_res.value
                label_lr.jump()

            sub_value = sub_res.value

            if sub_value.__class__ is constexpr[Nested]:
                _extend_fn(sub_value)
            else:
                _append_fn(sub_value)

        now += 1
        loop.jump()

        with label_finish:
            ret = constexpr[Result](constexpr[Matched], nested)
            label_return.jump()

        with label_fail:
            if now:
                state.reset(root_history)

            ret = constexpr[Result.mismatched]
            label_return.jump()

        with label_lr:
            match__ = match
            FINISH_, CONTINUE_, FAIL_ = FINISH, CONTINUE, FAIL

            def stacked_func_(ast: AST):
                def foreach(times: int, _extend_fn, _append_fn):
                    if times == most_:
                        return FINISH_
                    history = state.commit()
                    sub_res = match__(tokenizers, state)
                    if sub_res.status is Unmatched:
                        state.reset(history)
                        if times >= least_:
                            return FINISH_
                        return FAIL_

                    elif sub_res.status is FindLR:
                        if least_ is 0:
                            state.reset(history)
                            warnings.warn(f"Left recursion supporting is ambiguous with repeatable parser"
                                          f"({self}) that which couldn't fail.")
                            return FAIL_
                        return sub_res.value

                    sub_value = sub_res.value
                    if sub_value.__class__ is Nested:
                        _extend_fn(sub_value)
                    else:
                        _append_fn(sub_value)
                    return CONTINUE_

                now_ = now
                parsed_ = nested.copy()
                res = stacked_func(ast)

                if res.status is Unmatched:
                    return Result.mismatched if now_ < least_ else Result.match(parsed_)

                now_ += 1
                while True:
                    status_ = foreach(now_, parsed_.extend, parsed_.append)
                    if status_ is FINISH_:
                        return Result.match(parsed_)
                    elif status_ is CONTINUE_:
                        now_ += 1
                        continue
                    return Result.mismatched

            ret = constexpr[Result.find_lr](stacked_func_)
            label_return.mark()
            return ret

    self.match = seq_match


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


@Composed.as_fixed.case(None)
def do_nothing(self, lang):
    pass
