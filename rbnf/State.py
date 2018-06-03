from typing import Optional, Callable
from Redy.Magic.Classic import singleton
from .Trace import *

Context = 'Dict[str, AST]'


@singleton
class LRManager:
    state: 'State'

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.state.lr_name = None


LRManager: LRManager


class ContextRecovery:
    state: 'State'
    ctx: 'Context'

    def __init__(self, state: 'State'):
        self.ctx = state.ctx
        self.state = state

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.state.ctx = self.ctx


class State(Generic[T]):
    trace: Trace[Trace[T]]
    persistent_state: dict
    lr_name: Optional[str]
    lang: dict
    ctx: Context

    _new_one_factory: Callable[[], Trace[T]]

    def __init__(self, lang):
        self.lang = lang
        self.lr_name = None
        self.ctx = {}

        self.trace = Trace()
        self.trace.append(Trace())

        self._new_one_factory = Trace

    def left_recursion(self):
        LRManager.state = self
        return LRManager

    def leave_with_context_recovery(self):
        return ContextRecovery(self)

    @property
    def current(self):
        trace = self.trace
        return trace[trace.end_index]

    @property
    def max_fetched(self):
        return self.trace.max_fetched

    @property
    def end_index(self):
        """
        the number of tokenizers that've been parsed.
        """
        return self.trace.end_index

    def new_one(self):
        virtual_increment = False
        # real_increment = True

        trace = self.trace
        if trace.increment(self._new_one_factory) == virtual_increment:
            self.current.clear()

    def append(self, e: T):
        self.current.append(e)

    def commit(self):
        return self.trace.commit(), self.current.commit(), self.ctx

    def reset(self, history):
        base, branch, ctx = history
        self.ctx = ctx
        return self.trace.reset(base), self.current.reset(branch)

    def __contains__(self, item: T):
        return item in self.current

    def __str__(self):
        return self.trace.__str__()

    def __repr__(self):
        return self.__str__()
