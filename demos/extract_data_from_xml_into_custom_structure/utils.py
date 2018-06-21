from rbnf.Tokenizer import Tokenizer
from rbnf.AST import AST
from typing import Sequence


def to_str(tks: Sequence[Tokenizer]):
    return ''.join(each.value for each in tks)
