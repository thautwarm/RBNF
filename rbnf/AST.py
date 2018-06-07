from Redy.Typing import *
from Redy.Magic.Classic import record


def format_ast(self: 'AST', i: int):
    if isinstance(self, Named):
        content = self.format(i)
    elif isinstance(self, Nested):
        content = self.format(i)
    else:
        content = (' ' * i) + str(self)
    return content

class AST:
    pass


class Nested(AST, List[AST]):
    def format(self, i=0):
        return '\n'.join(format_ast(each, i + 1) for each in self)

    def __str__(self):
        return self.format(0)


@record
class Named(AST):
    name: str
    item: AST

    def format(self, i=0):
        named_indent_num = i + len(self.name) + 1
        indent = ' ' * i
        content = format_ast(self.item, named_indent_num)
        return f'{indent}{self.name}[\n{content}\n{indent}]'

    def __str__(self):
        return self.format(0)
