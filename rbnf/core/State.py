from typing import Callable, Set, Tuple
from Redy.Magic.Classic import singleton
from .Trace import *

Context = 'Dict[str, AST]'


class LRManager:
    __slots__ = ['state', 'record']
    state: 'State'
    record: Tuple[int, str]

    def __init__(self, state, record):
        self.state = state
        self.record = record

    def __enter__(self):
        self.state.lr.add(self.record)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.state.lr.remove(self.record)


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
    lr: Set[Tuple[int, str]]
    lang: dict
    ctx: Context

    _new_one_factory: Callable[[], Trace[T]]

    def __init__(self, lang, filename=None):
        self.lang = lang
        self.lr = set()
        self.filename = filename
        self.ctx = {}

        self.data = None

        self.trace = Trace()
        self.trace.append(Trace())

        self._new_one_factory = Trace

    def left_recursion(self, lr_record):

        return LRManager(self, lr_record)

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
