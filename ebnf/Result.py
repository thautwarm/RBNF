from Redy.ADT.Core import data
from Redy.Typing import *
from .Color import *


@data
class Status:
    Matched: ...
    Unmatched: ...
    FindLR: ...


Matched: Status = Status.Matched
Unmatched: Status = Status.Unmatched
FindLR: Status = Status.FindLR


class Result:
    __slots__ = ['status', 'value']

    status: Status
    value: T

    def __init__(self, status: Status, value: T):
        self.status = status
        self.value = value

    def __str__(self):
        return {
            Unmatched: lambda: Red("Unmatched"), Matched: lambda: Green(str(self.value)),
            FindLR   : lambda: Blue(f"Find left recursion.")
        }[self.status]()


unmatch = Result(Unmatched, None)
