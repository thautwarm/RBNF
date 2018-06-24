from .rbnf_asdl import *

bootstrap = {}
C = Literal.C
N = Literal.N

END = N('END')

CodeItem = PAtom.Named("CodeItem", code_item_enter_constraint, None, None)

AtomExpr = PAtom.Named("Atom", None, None, atom_rewrite)

Trail = PAtom.Named('Trail', None, None, trail_rewrite)


def and_rewrite(state: State):
    return AndASDL(state.ctx['value'])


And = PAtom.Named('And', None, None, and_rewrite)

Or = PAtom.Named('Or', None, None, or_rewrite)

Statement = PAtom.Named('Statement', None, None, stmt_rewrite)


def stmts_rewrite(state: State):
    return StmtsASDL([e for e in state.ctx['seq'] if not isinstance(e, Tokenizer)])


Statements = PAtom.Named('Statements', None, None, stmts_rewrite)

When = PAtom.Named('When', None, None, postfix_rewrite)

With = PAtom.Named('With', None, None, postfix_rewrite)

Rewrite = PAtom.Named('Rewrite', None, None, postfix_rewrite)

Ignore = PAtom.Named("Ignore", None, None, ignore_rewrite)

Import = PAtom.Named("Import", None, None, import_rewrite)

DefParser = PAtom.Named("DefParser", None, None, parser_rewrite)

DefLexer = PAtom.Named("DefLexer", None, None, lexer_rewrite)

bootstrap[CodeItem[1]] = PAtom.Any
bootstrap[When[1]] = C("when") @ "sign" + CodeItem.one_or_more @ "expr"
bootstrap[With[1]] = C("with") @ "sign" + CodeItem.one_or_more @ "expr"
bootstrap[Rewrite[1]] = C("rewrite") @ "sign" + CodeItem.one_or_more @ "expr"

bootstrap[AtomExpr[1]] = optimize(
        ((C('(') + Or @ "or" + C(')')) | (C('[') + Or @ "optional" + C(']')) | Name @ "name" | Str @ "str"))

bootstrap[Trail[1]] = optimize((C('~') @ "rev" + AtomExpr @ "atom" | AtomExpr @ "atom" + (
        C('+') @ "one_or_more" | C('*') @ "zero_or_more" | C('{') + Number(1, 2) @ "interval" + C('}')).optional) + (
                                       C('as') + Name @ "bind").optional)

bootstrap[And[1]] = Trail.one_or_more @ "value"

bootstrap[Or[1]] = optimize(And @ "head" + (C('|') + And).unlimited @ "tail")

import_syntax = optimize(
        (C('pyimport') @ "python" | C("import")) + Name @ "head" + (C('.') + (C('*') | Name)).unlimited @ "tail" + C(
                '.') + C('[') + (C('*') | Name.unlimited @ "import_items") + C(']'))

bootstrap[Import[1]] = optimize(import_syntax)

bootstrap[Ignore[1]] = optimize(C("ignore") + C('[') + Name.one_or_more @ "names" + C(']'))

parserc_syntax = Name @ "name" + C('::=') + C(
        '|').optional + Or @ "or" + When.optional @ "when" + With.optional @ "with" + Rewrite.optional @ "rewrite"
bootstrap[DefParser[1]] = optimize(parserc_syntax)

lexer_syntax = Name @ "name" + C('cast').optional @ "cast" + (C('as') + Name @ "new prefix").optional + C(':=') + C(
        '|').optional + Str.one_or_more @ "lexers"
bootstrap[DefLexer[1]] = optimize(lexer_syntax)

bootstrap[Statement[1]] = Ignore @ "ignore" | Import @ "import" | DefParser @ "parser" | DefLexer @ "lexer"
bootstrap[Statements[1]] = optimize(END.optional + (Statement + END.optional).unlimited @ "seq")
