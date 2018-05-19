from Redy.Collections import Traversal, Flow
from collections import OrderedDict
from typing import Dict, TypeVar, List, Callable, Iterable

TR = TypeVar('TR')
T = TypeVar('T')


class WellDict(OrderedDict):
    _miss_type: type

    def set_default_factory(self, type):
        self._miss_type = type

    def __missing__(self, key):
        self[key] = value = self._miss_type()
        return value


x = WellDict()


def well_group_by(fn):
    def inner(seq):
        ret = WellDict(list)
        ret.set_default_factory(list)

        for each in seq:
            ret[fn(each)].append(each)

        return ret

    return inner
