from rbnf.ParserC import *
from Redy.Magic.Classic import cast, record

_ = Atom.Any
C = Literal.C
R = Literal.R


def rewrite(state: State) -> Named:
    ctx = state.ctx
    name = ctx['tag1'].value
    subs = []
    cache = []
    if 'subs' in ctx:
        for each in ctx['subs']:
            if isinstance(each, Named):
                if cache:
                    subs.append(''.join(cache))
                    cache.clear()
                subs.append(each)
            else:
                each: Tokenizer
                cache.append(each.value)

        if cache:
            subs.append(''.join(cache))
            cache.clear()

    return Named(name, Nested(subs))


def constraint(tokenizers: Sequence[Tokenizer], state: State):
    context = state.ctx

    if 'tag2' not in context:
        return True
    return context["tag1"] == context["tag2"]


lang = {}
# definitions of parsers
xml = Atom.Named("XML", None, constraint, rewrite)
# block = Atom.Named("block", None, None, None)
Name = R("[a-zA-Z_]{1}[a-zA-Z0-9_]*")
# end = C('<') + C('/') + Name + C('>')
# begin = C('<') + Name + C('>')

imp_xml = (C('<') + Name @ "tag1" + C('>') + (xml | ~(C('<') + C('/') + Name + C('>')))(0, -1) @ "subs" + C('<') + C(
        '/') + Name @ "tag2" + C('>') | C('<') + Name @ "tag1" + C('/') + C('>'))

# imp_block = xml | ~(begin | end)

# lang[block[1]] = imp_block  # block[:] == [Atom.Named, "block", None, None, None]
lang[xml[1]] = imp_xml  # xml[:] == (Atom.Named, "XML", None, constraint, None]

"""
XML   ::= '<' TagName as tag1 '>'
            (XML | ~(begin | end))+
          '<' '/' TagName as tag2 '>'
Block ::= XML | Not ('<' TagName '>' | '<' '/' TagName '>')
"""


@cast(tuple)
def make_tokens(*args):
    return map(lambda it: Tokenizer("too known", it, 0, 0), args)


tokens = make_tokens("<", "my", ">", "x", "y", "z", "<", "my", ">", "x", "y", "z", '<', 'x', '>', '<', '/', 'x', '>',
                     '<', 'single', '/', '>',
                     "<", "/", "my", ">", "<", "/", "my", ">")
state = State(lang)
print(xml.match(tokens, state))
