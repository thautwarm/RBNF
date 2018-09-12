from ..ParserC import Composed, Atom, Parser, LRFunc
from ..Tokenizer import Tokenizer
from ..State import State
from ..Result import *
from ..AST import *
from Redy.Opt import feature, constexpr, const, goto, label

from typing import Sequence, List

staging = (const, constexpr)


@Atom.match.case(Atom.Any)
def _any_match(_, tokenizers, state):
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
def _bind_match(self: Atom, tokenizers, state):
    _, name, parser = self
    result = parser.match(tokenizers, state)

    if result.status is FindLR:
        lr_parser, stacked_func = result.value

        def stacked_func_(ast):
            stacked_result = stacked_func(ast)
            if stacked_result.status is Matched:
                state.ctx = state.ctx.copy()
                state.ctx[name] = stacked_result.value
            return stacked_result

        return Result.find_lr(lr_parser, stacked_func_)

    elif result.status is Matched:
        ctx = state.ctx = state.ctx.copy()
        ctx[name] = result.value

    return result


@Atom.as_fixed.case(Atom.Bind)
def as_fixed(self, lang):
    _, name_, parser_ = self
    parser_.as_fixed(lang)

    @feature(staging)
    def bind_match(tokenizers, state):
        name: const = name_
        match: const = parser_.match
        result = match(tokenizers, state)

        if result.status is constexpr[FindLR]:
            lr_parser, stacked_func = result.value

            def stacked_func_(ast):
                stacked_result = stacked_func(ast)
                if stacked_result.status is Matched:
                    state.ctx = state.ctx.copy()
                    state.ctx[name] = stacked_result.value
                return stacked_result

            return constexpr[Result.find_lr](lr_parser, stacked_func_)

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
        lr_parser, stacked_func = result.value

        def stacked_func_(ast: AST):
            stacked_result = stacked_func(ast)
            if stacked_result.status is Matched:
                state.ctx = state.ctx.copy()
                try:
                    state.ctx[name].append(stacked_result.value)
                except KeyError:
                    state.ctx[name] = [stacked_result.value]
            return stacked_result

        return Result.find_lr(lr_parser, stacked_func_)

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
    def push_match(tokenizers, state):
        name: const = name_
        match: const = parser_.match
        result = match(tokenizers, state)

        if result.status is constexpr[FindLR]:
            lr_parser, stacked_func = result.value

            def stacked_func_(ast):
                stacked_result = stacked_func(ast)
                if stacked_result.status is Matched:
                    state.ctx = state.ctx.copy()
                    try:
                        state.ctx[name].append(stacked_result.value)
                    except KeyError:
                        state.ctx[name] = [stacked_result.value]
                return stacked_result

            return constexpr[Result.find_lr](lr_parser, stacked_func_)

        elif result.status is constexpr[Matched]:
            ctx = state.ctx = state.ctx.copy()
            try:
                ctx[name].append(result.value)
            except constexpr[KeyError]:
                ctx[name] = [result.value]

        return result

    self.match = push_match

    return self


@Atom.match.case(Atom.Named)
def _named_match(self, tokenizers, state):
    _, name = self
    lang = state.lang
    parser, when, with_, rewrite = lang[name]
    if when and not when(tokenizers, state):
        return Result.mismatched

    lr_marker = (state.end_index, name)
    if name in state:
        if lr_marker in state.lr:
            return Result.mismatched

        def stacked_func(ast):
            return Result(Matched, ast)

        return Result.find_lr(self, stacked_func)

    with state.leave_with_context_recovery():
        state.append(name)
        state.ctx = {}
        history = state.commit()
        result = parser.match(tokenizers, state)
        if result.status is Matched:
            if with_ and not with_(tokenizers, state):
                return Result.mismatched
            return Result(
                Matched,
                rewrite(state) if rewrite else Named(name, result.value))

        elif result.status is FindLR:
            parser_obj, stacked_func = result.value

            if parser_obj is not self:

                def stacked_func_(ast: AST):
                    stacked_result = stacked_func(ast)
                    if stacked_result.status is Matched:
                        return Result.match(
                            rewrite(state) if rewrite else Named(
                                name, stacked_result.value))
                    return stacked_result

                return Result.find_lr(parser_obj, stacked_func_)
        else:
            return Result.mismatched

        # find lr and state.lr_name is name

        with state.left_recursion(lr_marker):

            state.reset(history)
            original_ctx = state.ctx.copy()

            result: Result = parser.match(tokenizers, state)
            if result.status is Unmatched:
                return result

            if with_ and not with_(tokenizers, state):
                return Result.mismatched

            head: Named = rewrite(state) if rewrite else Named(
                name, result.value)
            while True:
                with state.leave_with_context_recovery():
                    state.ctx = original_ctx.copy()
                    res = stacked_func(head)
                    if res.status is Unmatched:
                        break

                    head = rewrite(state) if rewrite else Named(
                        name, res.value)

            result.value = head
            return result


@Atom.as_fixed.case(Atom.Named)
def as_fixed(self, lang):
    _, name_ = self
    parser_, when_, with__, rewrite_ = lang[name_]
    parser_.as_fixed(lang)

    @feature(staging)
    def name_match(tokenizers, state: State):
        when: const = when_
        self_: const = self
        with_: const = with__
        name: const = name_
        rewrite: const = rewrite_
        mismatched: const = Result.mismatched
        match: const = parser_.match

        if constexpr[when]:
            if not when(tokenizers, state):
                return mismatched

        lr_marker = (state.end_index, name)
        if name in state:
            if lr_marker in state.lr:
                return mismatched

            def stacked_func(ast):
                return Result(Matched, ast)

            return constexpr[Result.find_lr](self_, stacked_func)

        with state.leave_with_context_recovery():
            state.append(name)
            state.ctx = {}
            history = state.commit()

            result = match(tokenizers, state)

            if result.status is constexpr[Matched]:
                if constexpr[with_]:
                    if not with_(tokenizers, state):
                        return mismatched

                return constexpr[Result](
                    constexpr[Matched], rewrite(state) if constexpr[rewrite]
                    else constexpr[Named](name, result.value))

            elif result.status is constexpr[FindLR]:
                lr_parser, stacked_func = result.value

                if lr_parser is not self_:
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
                                return Result.match(
                                    Named(name, stacked_result.value))
                            return stacked_result

                    return constexpr[Result.find_lr](lr_parser, stacked_func_)
            else:
                return mismatched

            # find lr and state.lr_name is name

            with state.left_recursion(lr_marker):
                state.reset(history)
                original_ctx = state.ctx.copy()

                result = match(tokenizers, state)

                if result.status is constexpr[Unmatched]:
                    return result

                if constexpr[with_]:
                    if not with_(tokenizers, state):
                        return mismatched

                head = rewrite(
                    state) if constexpr[rewrite] else constexpr[Named](
                        name, result.value)
                while True:
                    with state.leave_with_context_recovery():
                        state.ctx = original_ctx.copy()
                        res = stacked_func(head)
                        if res.status is constexpr[Unmatched]:
                            break

                        head = rewrite(
                            state) if constexpr[rewrite] else constexpr[Named](
                                name, res.value)

                result.value = head
                return result

    self.match = name_match


@Atom.as_fixed.case(Atom.Guard)
def _guard_as_fixed(self, lang):
    @feature(staging)
    def _guard_match(tokenizers: Sequence[Tokenizer], state: State) -> Result:
        match: const = self[1].match
        predicate: const = self[2]

        result = match(tokenizers, state)
        status = result.status
        if status is constexpr[Matched]:
            if not predicate(result.value, state):
                return constexpr[Result.mismatched]
            return result
        elif status is Unmatched:
            return result
        lr_parser, stacked_fn_ = result.value
        predicate_ = predicate
        matched = Matched
        mismatched = Result.mismatched

        def stacked_fn(ast):
            result = stacked_fn_(ast)
            if result.status is not matched or not predicate_(
                    result.value, state):
                return mismatched
            return result

        return constexpr[Result.find_lr](lr_parser, stacked_fn)

    return _guard_match


@Atom.match.case(Atom.Guard)
def _guard_match(self, tokenizers: Sequence[Tokenizer],
                 state: State) -> Result:

    result = self[1].match(tokenizers, state)
    status = result.status
    if status is Matched:
        if not self[2](result.value, state):
            return Result.mismatched
        return result
    elif status is Unmatched:
        return result

    lr_parser, stacked_fn_ = result.value

    def stacked_fn(ast: AST):
        result = stacked_fn_(ast)
        if result.status is not Matched or not self[2](result.value, state):
            return Result.mismatched
        return result

    return Result.find_lr(lr_parser, stacked_fn)


@Atom.as_fixed.case(None)
def do_nothing(self, lang):
    pass
