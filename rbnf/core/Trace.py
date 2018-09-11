from typing import Sequence, List, Generic, TypeVar
from ..color import *

T = TypeVar('T')


class Trace(Sequence[T], Generic[T]):
    def __len__(self) -> int:
        return self._virtual_len

    def __getitem__(self, i: int) -> T:
        if i >= self._virtual_len:
            raise IndexError
        return self._records[i]

    def __iter__(self):
        for i in range(self._virtual_len):
            yield self._records[i]

    def __init__(self):
        self._records: List[T] = []
        self._virtual_len = 0

    def clear(self):
        self._virtual_len = 0

    def commit(self):
        return self._virtual_len

    def reset(self, history: int):
        self._virtual_len = history

    def append(self, e: T):
        v_len = self._virtual_len
        if len(self._records) == v_len:
            self._records.append(e)
            self._virtual_len += 1
            return

        self._virtual_len += 1
        self._records[v_len] = e

    def increment(self, factory) -> bool:
        v_len = self._virtual_len
        if len(self._records) == v_len:
            self._records.append(factory())
            self._virtual_len += 1
            return True
        self._virtual_len += 1
        return False

    @property
    def end_index(self):
        return self._virtual_len - 1

    @property
    def max_fetched(self):
        return len(self._records)

    def __str__(self):
        content = ', '.join(
            Green(str(each)) if i < self._virtual_len else Red(str(each))
            for i, each in enumerate(self._records))
        return f'[{content}]'

    def __repr__(self):
        return self.__str__()
