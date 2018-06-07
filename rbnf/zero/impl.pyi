from .user_interface import *

__all__ = ['compile', 'ResultDescription']


class ZeroExp:
    def __call__(self, text: str) -> ResultDescription: ...


def compile(bnf_syntax: str, use: str = 'stmts') -> ZeroExp: ...
