from rbnf.ParserC import Literal, Context, Tokenizer, State, Atom as PAtom
from rbnf.AutoLexer.rbnf_lexer import *
from rbnf.CachingPool import ConstStrPool
from Redy.Magic.Classic import singleton
from .xml import XML, language_xml
from .common import Name, Str, Number


@singleton
class Const:
    def __ror__(self, item: str):
        return ConstStrPool.cast_to_const(item)


Const: Const

x: Tokenizer[str]
bootstrap = {}
ctx = Context()
C = Literal.C
N = Literal.N

END = N('END')

Atom = PAtom.Named("Atom", None, None, None)

Trail = PAtom.Named('Trail', None, None, None)

And = PAtom.Named('And', None, None, None)

Or = PAtom.Named('Or', None, None, None)

Statement = PAtom.Named('Statement', None, None, None)

Statements = PAtom.Named('Statements', None, None, None)

When = PAtom.Named('When', None, None, None)

With = PAtom.Named('With', None, None, None)

Rewrite = PAtom.Named('Rewrite', None, None, None)

Ignore = PAtom.Named("Ignore", None, None, None)

Import = PAtom.Named("Import", None, None, None)

DefParser = PAtom.Named("DefParser", None, None, None)

DefLexer = PAtom.Named("DefLexer", None, None, None)

bootstrap[When[1]] = C("when") + XML
bootstrap[With[1]] = C("with") + XML
bootstrap[Rewrite[1]] = C("rewrite") + XML

bootstrap[Atom[1]] = Name | Str | (C('(') + Str + C(')'))

bootstrap[Trail[1]] = (C('~') + Atom | Atom + (C('+') | C('*') | C('{') + Number(1, 2) + C('}')).optional)

bootstrap[And[1]] = Trail.one_or_more

bootstrap[Or[1]] = And + (C('|') + And).optional

ignore_syntax = C('ignore') + C('[') + Name.unlimited + C(']')
bootstrap[Ignore[1]] = ignore_syntax

import_syntax = C('import') + Name + (C('.') + (C('*') | Name)).unlimited
bootstrap[Import[1]] = import_syntax

parserc_syntax = Name + C('::=') + C('|').optional + Or + When.optional + With.optional + Rewrite.optional
bootstrap[DefParser[1]] = parserc_syntax

lexer_syntax = Name + C('cast').optional + (C('as') + Name).optional + C(':=') + C('|').optional + Str.one_or_more
bootstrap[DefLexer[1]] = lexer_syntax

bootstrap[Statement[1]] = Ignore | Import | DefParser | DefLexer
bootstrap[Statements[1]] = END.optional + (Statement + END.optional).unlimited
bootstrap.update(language_xml)

