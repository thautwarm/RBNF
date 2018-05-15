from typing import Sequence, List, Generic, Type
from Redy.Typing import T
from .Color import Red, Green


class Trace(Sequence[T], Generic[T]):

    def __len__(self) -> int:
        return self.virtual_length

    def __getitem__(self, i: int) -> T:
        if i >= self.virtual_length:
            raise IndexError
        return self._records[i]

    def __init__(self):
        self._records: List[T] = []
        self.virtual_length = 0

    @property
    def len(self):
        return self.virtual_length

    @property
    def max_fetched(self):
        return len(self._records)

    def commit(self):
        return self.virtual_length

    def reset(self, history: int):
        self.virtual_length = history

    def append(self, e: T):
        if len(self._records) == self.virtual_length:
            self._records.append(e)
            self.virtual_length += 1
            return
        self._records[self.virtual_length] = e
        self.virtual_length += 1

    def clear(self):
        self.virtual_length = 0

    def __str__(self):
        content = ', '.join(
                Green(str(each)) if i < self.virtual_length else Red(str(each)) for i, each in enumerate(self._records))
        return f'[{content}]'

    def __repr__(self):
        return self.__str__()



