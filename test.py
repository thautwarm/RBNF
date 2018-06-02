from rbnf import *
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
xml = Atom.Named("XML", None, constraint, rewrite)
Name = R("[a-zA-Z_]{1}[a-zA-Z0-9_]*")

imp_xml = (C('<') + Name @ "tag1" + C('>') + (xml | ~(C('<') + C('/') + Name + C('>')))(0, -1) @ "subs" + C('<') + C(
        '/') + Name @ "tag2" + C('>') | C('<') + Name @ "tag1" + C('/') + C('>'))


lang[xml[1]] = imp_xml

"""
XML   ::= | '<' Name as tag1 '>'
               (XML | ~('<' '/' Name '>'))*
            '<' '/' Name as tag1 '>'
          | '<' Name as tag1  '/' '>'
             
"""


@cast(tuple)
def make_tokens(*args):
    return map(lambda it: Tokenizer("too known", it, 0, 0), args)


tokens = make_tokens("<", "my", ">", "x", "y", "z", "<", "my", ">", "x", "y", "z", '<', 'x', '>', '<', '/', 'x', '>',
                     '<', 'single', '/', '>',
                     "<", "/", "my", ">", "<", "/", "my", ">")
state = State(lang)
print(xml.match(tokens, state))
