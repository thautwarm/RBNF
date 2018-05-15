from typing import Optional
from Redy.Magic.Classic import singleton
from .Trace import *


@singleton
class LRManager:
    state: 'State'

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.state.lr_name = None


LRManager: LRManager


class State(Generic[T]):
    trace: Trace[Trace[T]]
    persistent_state: dict
    lr_name: Optional[str]
    lang: dict

    def __init__(self, lang):
        self.lang = lang
        self.lr_name = None
        self.trace = Trace()
        current = self.current = Trace()
        self.trace.append(current)

    def do_left_recursion(self):
        LRManager.state = self
        return LRManager

    @property
    def counted(self):
        return self.trace.len - 1

    def new_one(self):
        trace = self.trace
        if trace.max_fetched > trace.len:
            idx = trace.len
            trace.virtual_length += 1
            current = self.current = trace[idx]
            current.clear()


            return
        self.current = current = Trace()
        trace.append(current)

    def append(self, e: T):
        self.current.append(e)

    def commit(self):
        return self.trace.commit(), self.current.commit()

    def reset(self, history):
        base, branch = history
        return self.trace.reset(base), self.current.reset(branch)

    def __contains__(self, item: T):
        return item in self.current

    def __str__(self):
        return str(self.trace)

    def __repr__(self):
        return self.__str__()
