from Redy.Magic.Classic import record

ConstString = str


@record
class Tokenizer:
    name: ConstString
    value: str  # maybe const string
    lineno: int
    colno: int
