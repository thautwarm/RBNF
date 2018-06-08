from Redy.ADT.Core import data
from Redy.Typing import *
from .Color import *

__all__ = ['Status', 'Result', 'Matched', 'Unmatched', 'FindLR']


@data
class Status:
    Matched: ...
    Unmatched: ...
    FindLR: ...


Matched: Status = Status.Matched
Unmatched: Status = Status.Unmatched
FindLR: Status = Status.FindLR


class Result:
    mismatched: 'Result'
    __slots__ = ['status', 'value']

    status: Status
    value: T

    def __init__(self, status: Status, value: T):
        self.status = status
        self.value = value

    def __str__(self):
        return {
            Unmatched: lambda: Red("Unmatched"), Matched: lambda: Green(str(self.value)),
            FindLR: lambda: Blue(f"Find left recursion.")
        }[self.status]()

    @staticmethod
    def match(value: T) -> 'Result':
        return Result(Matched, value)

    @staticmethod
    def find_lr(func) -> 'Result':
        return Result(FindLR, func)

    @staticmethod
    def mismatch():
        return _mismatch


_mismatch = Result(Unmatched, None)
Result.mismatched = _mismatch
