from .Tokenizer import Tokenizer
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
    def match(token: Tokenizer):
        return token.value is const_str

    return match


def make_name_matcher(name: str):
    def match(token: Tokenizer):
        return token.value is name

    return match


def make_name_and_const_str_matcher(name: str, const_str: str):
    def match(token: Tokenizer):
        return token.value is const_str and token.name is name

    return match