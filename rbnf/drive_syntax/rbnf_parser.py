"""
import RuikoML.*

Atom ::=
    | Name
    | Str
    | '(' Or ')'

Trail ::=
    | Atom ['+' | '*' | '{' Number{1, 2} '}']
    | '~' Atom

And   ::=
    | Trail+

Or    ::=
    | And ('|' And)*

Statement ::=
    | 'ignore' '[' Name ']'
    | 'import' Name ('.' ('*' | Name))*
    | Name '::=' ['|']  Or [Clauses]
    | Name ['cast'] ['as' Name] ':=' ['|'] Str+ [Clauses]

Clauses ::=
    [When] [With] [Where] [Rewrite]

When ::= 'when' Expr

With ::= 'with' Expr

Where ::= 'where' Expr

Rewrite ::= 'rewrite' Lambda

Statements ::=
    | Statement (END Statement)*


Lang.XML:
    import std.Name
    XML ::= '<' Name as t1 '>'
                (XML | ~('<' Name '>'))*
            '<' Name as t2 '>'
            with t1 = t2

"""

from rbnf.ParserC import Literal, Context, Tokenizer, State, Atom as PAtom
from rbnf.AutoLexer.rbnf_lexer import *
from rbnf.CachingPool import ConstStrPool
from Redy.Magic.Classic import singleton


@singleton
class Const:
    def __ror__(self, item: str):
        return ConstStrPool.cast_to_const(item)


Const: Const

x: Tokenizer[str]
lang = {}
ctx = Context()
C = Literal.C
N = Literal.N

Name = N('Name')
Str = N('Str')
Number = N('Number')
END = N('END')

Atom = PAtom.Named("Atom", None, None, None)

Trail = PAtom.Named('Trail', None, None, None)

And = PAtom.Named('And', None, None, None)

Or = PAtom.Named('Or', None, None, None)

Statement = PAtom.Named('Statement', None, None, None)

Statements = PAtom.Named('Statements', None, None, None)

Ignore = PAtom.Named("Ignore", None, None, None)

Import = PAtom.Named("Import", None, None, None)

DefParser = PAtom.Named("DefParser", None, None, None)

DefLexer = PAtom.Named("DefLexer", None, None, None)

lang[Atom[1]] = Name | Str | (C('(') + Str + C(')'))

lang[Trail[1]] = (C('~') + Atom | Atom + (C('+') | C('*') | C('{') + Number(1, 2) + C('}')).optional)

lang[And[1]] = Trail.one_or_more

lang[Or[1]] = And + (C('|') + And).optional

ignore_syntax = C('ignore') + C('[') + Name.unlimited + C(']')
lang[Ignore[1]] = ignore_syntax

import_syntax = C('import') + Name + (C('.') + (C('*') | Name)).unlimited
lang[Import[1]] = import_syntax

parserc_syntax = Name + C('::=') + C('|').optional + Or
lang[DefParser[1]] = parserc_syntax

lexer_syntax = Name + C('cast').optional + (C('as') + Name).optional + C(':=') + C('|').optional + Str.one_or_more
lang[DefLexer[1]] = lexer_syntax

lang[Statement[1]] = Ignore | Import | DefParser | DefLexer
lang[Statements[1]] = END.optional + Statement + (END + Statement).unlimited
