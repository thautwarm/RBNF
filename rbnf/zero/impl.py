from rbnf.std.compiler import *
from Redy.Opt.ConstExpr import constexpr, const

try:
    from Redy.Opt.ConstExpr import feature
except:
    from Redy.Opt.ConstExpr import optimize as feature
from .user_interface import ResultDescription

__all__ = ['compile', 'ResultDescription']


class ZeroExp:
    def __init__(self, bnf_syntax: str, use: str, custom_lexer_wrapper=None):
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

        @feature
        def match(text) -> ResultDescription:
            _state = State(constexpr[lang])
            _wrapper: const = custom_lexer_wrapper
            _lexer: const = lexer

            _tokens = tuple(_wrapper(_lexer(text)) if constexpr[custom_lexer_wrapper] else _lexer(text))
            _result: Result = constexpr[top_parser.match](_tokens, _state)
            return constexpr[ResultDescription](_state, _result.value, _tokens)

        self.match = match


def compile(bnf_syntax: str, use: str = None, custom_lexer_wrapper=None):
    bnf_syntax = bnf_syntax
    return ZeroExp(bnf_syntax, use, custom_lexer_wrapper=custom_lexer_wrapper)
