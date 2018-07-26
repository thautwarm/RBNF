from Redy.Magic.Pattern import Pattern
from collections import OrderedDict
from typing import Dict, TypeVar, List, Callable, Iterable
from .ParserC import Parser, Composed

TR = TypeVar('TR')
T = TypeVar('T')


class WellDict(OrderedDict):
    _miss_type: type

    def set_default_factory(self, type):
        self._miss_type = type

    def __missing__(self, key):
        self[key] = value = self._miss_type()
        return value


def well_group_by(fn):
    def inner(seq):
        ret = WellDict()
        ret.set_default_factory(list)

        for each in seq:
            ret[fn(each)].append(each)

        return ret

    return inner


@Pattern
def optimize(parser: Parser) -> Parser:
    return parser[0]


@optimize.case(Composed.And)
def optimize(and_: Composed.And) -> Parser:
    parsers: List[Parser] = and_[1]
    return optimize(parsers[0]) if len(parsers) is 1 else Composed.And(list(map(optimize, parsers)))


@optimize.case(Composed.Or)
def optimize(or_: Composed.Or) -> Parser:
    parsers: List[Parser] = or_[1]

    if len(parsers) is 1:
        return optimize(parsers[0])

    ands = [and_[1] if and_[0] is Composed.And else [and_] for and_ in parsers]
    groups: Dict[str, List[List[Parser]]] = well_group_by(lambda x: str(x[0]))(ands)
    cases = []

    for each_group in groups.values():
        if len(each_group) is 1:
            each = each_group[0]
            cases.append(optimize(Composed.And(each)))

        elif any(map(lambda x: len(x) is 1, each_group)):
            left = list(map(lambda x: Composed.And(x[1:]), filter(lambda x: len(x) is not 1, each_group)))
            head = next(filter(lambda x: len(x) is 1, each_group))[0]
            cases.append(Composed.And([optimize(head), optimize(Composed.Or(left))(0, 1)]))

        else:
            head: Parser = each_group[0][0]
            left = list(map(lambda x: Composed.And(x[1:]), each_group))
            cases.append(Composed.And([optimize(head), optimize(Composed.Or(left))]))

    if len(cases) is 1:
        return cases[0]
    return Composed.Or(cases)


@optimize.case(any)
def optimize(_) -> Parser: return _
