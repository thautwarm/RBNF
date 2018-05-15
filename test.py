from ebnf.State import *
from ebnf.ParserC import *
from ebnf.CachingPool import *
from Redy.Magic.Classic import cast
C = Literal.C
R = Literal.R

def constraint(tokenizers: Sequence[Tokenizer], state: State, context: Context):
    print(context)
    if 'tag2' not in context:
        return True
    return context["tag1"] == context["tag2"]


lang  = {}
# definitions of parsers
xml   = Atom.Named("XML", None, constraint, None)
block = Atom.Named("block", None, None, None)

end   = C('<') + C('/') + R("[a-zA-Z_]{1}[a-zA-Z0-9_]*") + C('>')
begin = C('<') + R("[a-zA-Z_]{1}[a-zA-Z0-9_]*") + C('>')

imp_xml = (C('<')
           + R("[a-zA-Z_]{1}[a-zA-Z0-9_]*") @ "tag1" +
           C('>')
           + block(0, -1) +
           C('<') +
           C('/')
           + R("[a-zA-Z_]{1}[a-zA-Z0-9_]*") @ "tag2" +
           C('>'))

imp_block = xml | ~(begin | end)

lang[block[1]] = imp_block #  block[:] == [Atom.Named, "block", None, None, None]
lang[xml[1]] = imp_xml     #  xml[:] == (Atom.Named, "XML", None, constraint, None]

"""
XML   ::= '<' TagName as tag1 '>'
            (XML | ~(begin | end))+
          '<' '/' TagName as tag2 '>'
Block ::= XML | Not ('<' TagName '>' | '<' '/' TagName '>')
"""

@cast(tuple)
def make_tokens(*args):
    return map(lambda it: Tokenizer("too known", it, 0, 0), args)


tokens = make_tokens("<", "my", ">",
                        "x", "y", "z",
                        "<", "my", ">",
                            "x", "y", "z",
                        "<", "/", "my", ">",
                     "<", "/", "my",">")
context = {}
state = State(lang)
print(xml.match(tokens, state, context))