from ..ParserC import Composed, Atom, Parser, LRFunc
from ..Tokenizer import Tokenizer
from ..State import State
from ..Result import *
from ..AST import *
from Redy.Opt import feature, constexpr, const, goto, label

from typing import Sequence, List

staging = (const, constexpr)


@Atom.match.case(Atom.Any)
def _any_match(_, tokenizers: Sequence[Tokenizer], state: State) -> Result:
    try:
        token = tokenizers[state.end_index]
    except IndexError:
        return Result.mismatched
    state.new_one()
    return Result.match(token)


@Atom.as_fixed.case(Atom.Any)
def as_fixed(self, _):
    @feature(staging)
    def any_match(tokenizers, state):
        try:
            token = tokenizers[state.end_index]
        except IndexError:
            return constexpr[Result.mismatched]
        state.new_one()
        return constexpr[Result.match](token)

    self.match = any_match


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


@Atom.as_fixed.case(Atom.Bind)
def as_fixed(self, lang):
    _, name_, parser_ = self
    parser_.as_fixed(lang)

    @feature(staging)
    def bind_match(tokenizers: Sequence[Tokenizer], state: State):
        name: const = name_
        match: const = parser_.match
        result = match(tokenizers, state)

        if result.status is constexpr[FindLR]:
            stacked_func = result.value

            def stacked_func_(ast):
                stacked_result = stacked_func(ast)
                if stacked_result.status is Matched:
                    state.ctx = state.ctx.copy()
                    state.ctx[name] = stacked_result.value
                return stacked_result

            return constexpr[Result.find_lr](stacked_func_)

        elif result.status is constexpr[Matched]:
            ctx = state.ctx = state.ctx.copy()
            ctx[name] = result.value

        return result

    self.match = bind_match
    return self


@Atom.match.case(Atom.Push)
def _push_match(self: Atom, tokenizers: Sequence[Tokenizer], state: State):
    _, name, parser = self
    result = parser.match(tokenizers, state)

    if result.status is FindLR:
        stacked_func: LRFunc = result.value

        def stacked_func_(ast: AST):
            stacked_result = stacked_func(ast)
            if stacked_result.status is Matched:
                state.ctx = state.ctx.copy()
                try:
                    state.ctx[name].append(stacked_result.value)
                except KeyError:
                    state.ctx[name] = [stacked_result.value]
            return stacked_result

        return Result.find_lr(stacked_func_)

    elif result.status is Matched:
        ctx = state.ctx = state.ctx.copy()
        try:
            ctx[name].append(result.value)
        except KeyError:
            ctx[name] = [result.value]
    return result


@Atom.as_fixed.case(Atom.Push)
def as_fixed(self, lang):
    _, name_, parser_ = self
    parser_.as_fixed(lang)

    @feature(staging)
    def push_match(tokenizers: Sequence[Tokenizer], state: State):
        name: const = name_
        match: const = parser_.match
        result = match(tokenizers, state)

        if result.status is FindLR:
            stacked_func: LRFunc = result.value

            def stacked_func_(ast: AST):
                stacked_result = stacked_func(ast)
                if stacked_result.status is Matched:
                    state.ctx = state.ctx.copy()
                    try:
                        state.ctx[name].append(stacked_result.value)
                    except KeyError:
                        state.ctx[name] = [stacked_result.value]
                return stacked_result

            return constexpr[Result.find_lr](stacked_func_)

        elif result.status is constexpr[Matched]:
            ctx = state.ctx = state.ctx.copy()
            try:
                ctx[name].append(result.value)
            except KeyError:
                ctx[name] = [result.value]
        return result

    self.match = push_match
    return self


@Atom.match.case(Atom.Named)
def _named_match(self: Atom, tokenizers: Sequence[Tokenizer], state: State):
    _, name = self
    lang = state.lang
    parser, when, with_, rewrite = lang[name]
    if when and not when(tokenizers, state):
        return Result.mismatched

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
            original_ctx = state.ctx.copy()

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
                    state.ctx = original_ctx.copy()
                    res = stacked_func(head)
                    if res.status is Unmatched:
                        break

                    # assert res.status is Matched
                    head = rewrite(state) if rewrite else Named(name, res.value)

            result.value = head
            return result


@Atom.as_fixed.case(Atom.Named)
def as_fixed(self, lang):
    _, name = self
    parser_, when_, with__, rewrite_ = lang[name]
    parser_.as_fixed(lang)

    @feature(staging)
    def name_match(tokenizers, state):
        when: const = when_
        with_: const = with__
        rewrite: const = rewrite_
        mismatched: const = Result.mismatched
        match: const = parser_.match

        if constexpr[when]:
            if not when(tokenizers, state):
                return mismatched

        if name in state:
            if state.lr_name:
                return mismatched

            state.lr_name = name

            def stacked_func(ast: AST):
                return Result(Matched, ast)

            return constexpr[Result.find_lr](stacked_func)

        with state.leave_with_context_recovery():
            state.append(name)
            state.ctx = {}

            result = match(tokenizers, state)

            if result.status is constexpr[Matched]:
                if constexpr[with_]:
                    if not with_(tokenizers, state):
                        return mismatched

                return constexpr[Result](constexpr[Matched],
                                         rewrite(state) if constexpr[rewrite] else constexpr[Named](name, result.value))

            elif result.status is constexpr[FindLR]:
                stacked_func = result.value

                if state.lr_name is not name:
                    if constexpr[rewrite]:
                        def stacked_func_(ast: AST):
                            stacked_result = stacked_func(ast)
                            if stacked_result.status is Matched:
                                return Result.match(rewrite(state))
                            return stacked_result
                    else:
                        def stacked_func_(ast: AST):
                            stacked_result = stacked_func(ast)
                            if stacked_result.status is Matched:
                                return Result.match(Named(name, stacked_result.value))
                            return stacked_result

                    return constexpr[Result.find_lr](stacked_func_)
            else:
                return mismatched

            # find lr and state.lr_name is name

            with state.left_recursion():
                original_ctx = state.ctx.copy()

                result = match(tokenizers, state)

                if result.status is constexpr[Unmatched]:
                    return result

                # assert result.status is not FindLR

                if constexpr[with_]:
                    if not with_(tokenizers, state):
                        return mismatched

                head = rewrite(state) if constexpr[rewrite] else constexpr[Named](name, result.value)
                # stack jumping
                while True:
                    with state.leave_with_context_recovery():
                        state.ctx = original_ctx.copy()
                        res = stacked_func(head)
                        if res.status is Unmatched:
                            break

                        # assert res.status is Matched
                        head = rewrite(state) if constexpr[rewrite] else constexpr[Named](name, res.value)

                result.value = head
                return result

    self.match = name_match


@Atom.as_fixed.case(None)
def do_nothing(self, lang):
    pass
