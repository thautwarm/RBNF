from pprint import pprint
from ebnf.State import *
from ebnf.ParserC import *
from ebnf.CachingPool import *


def constraint(tokenizers: Sequence[Tokenizer], state: State, context: Context):
    print(context)
    if 'tag2' not in context:
        return True
    return context["tag1"] == context["tag2"]


lang = {}
xml: Atom = Atom.Named("XML", None, constraint, None)
block = Atom.Named("block", None, None, None)

end = Literal.C('<') + Literal.C('/') + Literal.R("[a-zA-Z_]{1}[a-zA-Z0-9_]*") + Literal.C('>')
begin = Literal.C('<') + Literal.R("[a-zA-Z_]{1}[a-zA-Z0-9_]*") + Literal.C('>')

imp_xml = (Literal.C('<')
           + Literal.R("[a-zA-Z_]{1}[a-zA-Z0-9_]*") @ "tag1" +
           Literal.C('>')
           + block(0, -1) +
           Literal.C('<') +
           Literal.C('/')
           + Literal.R("[a-zA-Z_]{1}[a-zA-Z0-9_]*") @ "tag2" +
           Literal.C('>'))

imp_block = xml | Composed.AnyNot(Composed.Or([begin, end]))

lang[block[1]] = imp_block
lang[xml[1]] = imp_xml
"""
XML   ::= '<' TagName as tag1 '>'
            (XML | Not)+
          '<' '/' TagName as tag2 '>'

Block ::= XML | Not ('<' TagName '>' | '<' '/' TagName '>')
"""
def make_tokens(*args):
    return list(map(lambda it: Tokenizer("too known", it, 0, 0), args))


tokens = make_tokens("<", "my", ">",
                        "x", "y", "z",
                        "<", "my", ">",
                            "x", "y", "z",
                        "<", "/", "my", ">",
                     "<", "/", "my",">")
context = {}
state = State(lang)
print(xml.match(tokens, state, context))

