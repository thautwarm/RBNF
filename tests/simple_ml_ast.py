import typing
import operator
from functools import reduce

Hint = typing.NamedTuple

globals()['Hint'] = object


class Eq:
    n: int

    def __init__(self, *args):
        annotations = getattr(self, '__annotations__', None)
        if annotations is None:
            self.n = 0
            return
        self.n = len(annotations)
        for k, v in zip(annotations, args):
            setattr(self, k, v)

    def __iter__(self):
        for _ in self.__annotations__:
            yield getattr(self, _)

    def __eq__(self, other):
        if self.__class__ is not other.__class__:
            return False
        return all(
            getattr(self, k) == getattr(other, k)
            for k in self.__annotations__)

    def __hash__(self):
        return reduce(operator.xor,
                      (hash(getattr(self, e)) for e in self.__annotations__),
                      hash(self.__class__))

    def __str__(self):
        return repr(self)

    def update(self, update_pairs):
        if isinstance(update_pairs, dict):
            update_pairs = update_pairs.items()

        cls = self.__class__
        new_one = cls.__new__(cls)
        new_one.n = self.n
        annotations = getattr(self, 'annotations', None)
        if annotations is not None:
            for k, v in zip(annotations, self):
                setattr(self, k,
                        next((v for _k, _v in update_pairs if _k == k), v))

    def collect(self, which: typing.Callable[['Eq'], bool], nested=False):
        for each in self:
            if isinstance(each, Eq) and which(each):
                yield each
                if nested:
                    yield from each.collect(which, True)


class UniqueHash:
    def __hash__(self):
        return id(self)


class Unit(Eq):
    def __repr__(self):
        return '()'


unit = Unit()


class Const(Eq, Hint):
    repr: typing.Any

    def __repr__(self):
        return repr(self.repr)


class Id(Eq, Hint):
    repr_str: str

    def __repr__(self):
        return self.repr_str


class Lam(Eq, Hint):
    arg: 'Id'
    annotate: 'TypeTerm'
    ret: 'Term'

    def __repr__(self):
        if not self.annotate:
            return 'λ{!r}.{!r}'.format(self.arg, self.ret)
        return 'λ{!r}: {!r}.{!r}'.format(self.arg, self.annotate, self.ret)


class App(Eq, Hint):
    fn: 'Term'
    arg: 'Term'

    def __repr__(self):
        return '{} {}'.format(self.fn, self.arg)


class Let(Eq, Hint):
    """
    for python is lazy in terms of function definitions,
    `let rec` is forced to take place here.
    """
    tag: str
    annotate: 'TypeTerm'
    value: 'Term'
    do: 'Term'

    def __repr__(self):
        annotate = self.annotate
        annotate_str = ': {!r}'.format(annotate) if annotate else ''

        return 'let {}{} = {!r} in {!r}'.format(self.tag, annotate_str,
                                                self.value, self.do)


class If(Eq, Hint):
    test: 'Term'
    body: 'Term'
    else_do: 'Term'

    def __repr__(self):
        return 'if {!r} then {!r} else {!r}'.format(self.test, self.body,
                                                    self.else_do)


class Tuple(Eq, Hint):
    items: typing.Tuple['Term', ...]

    def __repr__(self):
        return '({})'.format(', '.join(map(repr, self.items)))


class TypeTerm:
    def __str__(self):
        return repr(self)

    pass


class TypeSym(Eq, TypeTerm, Hint):
    name: str

    def __repr__(self):
        return self.name


class TypeSlot(Eq, TypeTerm, Hint):
    name: str

    def __repr__(self):
        return '\'{}'.format(self.name)


class TypeInduct(Eq, TypeTerm, Hint):
    sym: TypeSym
    ty: TypeTerm

    def __repr__(self):
        return '{!r} of {!r}'.format(self.sym, self.ty)


class TypeDef(Eq, TypeTerm, Hint):
    name: str
    args: typing.Tuple[str]
    impl: TypeTerm

    def __repr__(self):
        return 'type {}{} = {!r}'.format(
            self.name, '[{}]'.format(', '.join(
                map(lambda _: '\'' + _, self.args)))
            if self.args else "", self.impl)


class TypeAbbr(Eq, TypeTerm, Hint):
    name: str
    impl: TypeTerm

    def __repr__(self):
        return 'type {} = {!r}'.format(self.name, self.impl)


class TypeJoin(Eq, TypeTerm, Hint):
    components: typing.Tuple['TypeTerm']

    def __repr__(self):
        return ' * '.join(map(repr, self.components))


class TypeFunction(Eq, TypeTerm, Hint):
    left: TypeTerm
    right: TypeTerm

    def __repr__(self):
        right_str = ('({!r})'.format
                     if not isinstance(self.right, (TypeSym, TypeSlot)) else
                     repr)(self.right)
        return '{!r} -> {}'.format(self.left, right_str)


class Annotate(Eq, Hint):
    term: "Term"
    type: TypeTerm

    def __repr__(self):
        return '{!r} : {!r}'.format(self.term, self.type)


class Stmts(Eq, Hint):
    terms: typing.Tuple['Term']

    def __repr__(self):
        return '{{\n{}\n}}'.format('\n'.join(map(repr, self.terms)))


Term = typing.Union[Id, Let, Lam, App, Const, Stmts, Annotate]
