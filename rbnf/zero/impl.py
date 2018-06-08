from rbnf.std.compiler import *
from .user_interface import ResultDescription

__all__ = ['compile', 'ResultDescription']


class ZeroExp:
    def __init__(self, bnf_syntax: str, use: str):
        state = State(bootstrap)
        tokens = tuple(rbnf_lexing(bnf_syntax))
        result = Statements.match(tokens, state)

        if result.status is Unmatched:
            max_fetched = state.max_fetched
            tk: Tokenizer = tokens[max_fetched]
            before = recover_codes(tokens[max_fetched - 10:max_fetched])
            later = recover_codes(tokens[max_fetched: max_fetched + 10])
            raise SyntaxError("Error at line {}, col {}, see details:\n{}", tk.lineno, tk.colno,
                              Green(before) + Red(later))

        asdl = result.value
        ctx = create_ctx()
        visit(asdl, ctx)
        lexer = ctx['lex']
        lang = ctx['lang']
        if use is None:
            for end in asdl.value[::-1]:
                if isinstance(end, ParserASDL):
                    top_parser = ctx[end.name]
                    break
            else:
                raise ValueError("No top parser found!")

        else:
            top_parser = ctx[use]

        self._top_parser = top_parser
        self._lang = lang
        self._lexer = lexer
        self.ctx = ctx

    def match(self, text) -> ResultDescription:
        _state = State(self._lang)
        _tokens = tuple(self._lexer(text))
        _result: Result = self._top_parser.match(_tokens, _state)
        return ResultDescription(_state, _result.value, _tokens)


def compile(bnf_syntax: str, use: str = None):
    bnf_syntax = "import std.common.[*]\n" + bnf_syntax
    return ZeroExp(bnf_syntax, use)
