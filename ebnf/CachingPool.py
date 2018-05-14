from Redy.Magic.Classic import singleton


@singleton
class ConstStrPool:
    __slots__ = []
    _pool: dict = {}

    @classmethod
    def cast_to_const(cls, string: str):
        if string not in cls._pool:
            cls._pool[string] = string
        return cls._pool[string]
