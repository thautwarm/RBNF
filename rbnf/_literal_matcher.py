from .Tokenizer import Tokenizer
from .CachingPool import ConstStrPool
import re


def make_regex_matcher(regex_template: str):
    regex = re.compile(regex_template)

    def match(token: Tokenizer):
        return regex.match(token.value)

    return match


def make_runtime_str_matcher(runtime_str: str):
    def match(token: Tokenizer):
        return token.value == runtime_str

    return match


def make_const_str_matcher(const_str: str):
    const_str = ConstStrPool.cast_to_const(const_str)

    def match(token: Tokenizer):
        return token.value is const_str

    return match


def make_name_matcher(name: str):
    name = ConstStrPool.cast_to_const(name)

    def match(token: Tokenizer):
        return token.name is name

    return match


def make_name_and_const_str_matcher(name: str, const_str: str):
    name = ConstStrPool.cast_to_const(name)
    const_str = ConstStrPool.cast_to_const(const_str)

    def match(token: Tokenizer):
        return token.value is const_str and token.name is name

    return match
