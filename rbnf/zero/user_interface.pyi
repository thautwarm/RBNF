from rbnf.core.ParserC import State, Tokenizer
from typing import Generic, TypeVar, Sequence

T = TypeVar('T')

__all__ = ['ResultDescription']


class ResultDescription(Generic[T]):
    state: State
    result: T
    tokens: Sequence[Tokenizer]

    def __init__(self, state: State, result: T, tokens: Sequence[Tokenizer]): ...


