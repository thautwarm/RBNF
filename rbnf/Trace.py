from typing import Sequence, List, Generic, TypeVar
from .Color import *

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
                Green(str(each)) if i < self._virtual_len else Red(str(each)) for i, each in enumerate(self._records))
        return f'[{content}]'

    def __repr__(self):
        return self.__str__()

# class Trace(Sequence[T], Generic[T]):
#
#     def __len__(self) -> int:
#         return self.virtual_length
#
#     def __getitem__(self, i: int) -> T:
#         if i >= self.virtual_length:
#             raise IndexError
#         return self._records[i]
#
#     def __init__(self):
#         self._records: List[T] = []
#         self.virtual_length = 0
#
#     def check(self):
#         try:
#             assert self.virtual_length <= self.max_fetched
#         except AssertionError:
#             raise AssertionError(f"Requires: {self.virtual_length} <= {self.max_fetched}!")
#
#     @property
#     def len(self):
#         return self.virtual_length
#
#     @property
#     def max_fetched(self):
#         return len(self._records)
#
#     def commit(self):
#         return self.virtual_length
#
#     def reset(self, history: int):
#         self.virtual_length = history
#
#     def append(self, e: T):
#         v_len = self.virtual_length
#         if len(self._records) == v_len:
#             self._records.append(e)
#             self.virtual_length += 1
#             return
#
#         self.virtual_length += 1
#         self._records[v_len] = e
#
#     def clear(self):
#         self.virtual_length = 0
#
