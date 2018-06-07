from Redy.Magic.Classic import record
from typing import Tuple
from ..ParserC import State, Tokenizer


@record
class ResultDescription:
    state: State
    result: object
    tokens: Tuple[Tokenizer, ...]
