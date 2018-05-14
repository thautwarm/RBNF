from .Trace import *


class State(Generic[T]):
    trace: Trace[Trace[T]]
    persistent_state: dict

    def __init__(self):
        self.trace = Trace()
        current = self.current = Trace()
        self.trace.append(current)

    @property
    def counted(self):
        return self.trace.len - 1

    def new_one(self):
        trace = self.trace
        if trace.max_fetched > trace.len:
            current = self.current = trace[trace.len]
            current.clear()
            current.virtual_length += 1

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

    def __str__(self):
        return str(self.trace)

    def __repr__(self):
        return self.__str__()
