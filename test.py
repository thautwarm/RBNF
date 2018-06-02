from rbnf.drive_syntax.xml import language_xml, XML, imp_xml
from rbnf.drive_syntax.rbnf_parser import rbnf_lexing
from rbnf import Tokenizer, State, ConstStrPool

from Redy.Magic.Classic import cast


@cast(tuple)
def make_tokens(args):
    return map(lambda it: Tokenizer("too known", it, 0, 0), args)


tokens = rbnf_lexing(''.join(
        ["<", "my", ">", "x", "y", "z", "<", "my", ">", "x", "y", "z", '<', 'x', '>', '<', '/', 'x', '>', '<', 'single',
         '/', '>', "<", "/", "my", ">", "<", "/", "my", ">"]))

tokens = [e for e in tokens if e.name != 'END']
for e in tokens:
    print(e)

state = State(language_xml)

print(XML.match(tokens, state))
