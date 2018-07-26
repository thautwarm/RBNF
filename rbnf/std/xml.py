from ..core.ParserC import *
from .common import Name
from rbnf.core.Optimize import optimize

_ = Atom.Any
C = Literal.C
V = Literal.V
N = Literal.N


def rewrite(state: State) -> Named:
    ctx = state.ctx
    name = ctx['tag1'].value

    return Named(name, Nested(tuple(ctx.get('subs', ()))))


def constraint(tokenizers: Sequence['Tokenizer'], state: State):
    context = state.ctx
    if 'tag2' not in context:
        return True
    return context["tag1"].value == context["tag2"].value


language_xml = {}
XML = Atom.Named("XML")

# @formatter:off
imp_xml = optimize(C('<') + Name @ "tag1" + C('>')
                   + (XML | ~(C('<') + C('/') + Name + C('>')))(0, -1) @ "subs"
                   + C('<') + C('/') + Name @ "tag2" + C('>')
                   | C('<') + Name @ "tag1" + C('/') + C('>')), None, constraint, rewrite
# @formatter:on
language_xml[XML[1]] = imp_xml
