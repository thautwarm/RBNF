from rbnf.core.Tokenizer import Tokenizer
from rbnf.easy import ze
from rbnf.core.AST import Named


def test_lr(fixed=False):
    ze_exp = ze.compile("""A ::= A 'b' | 'a'""")
    if fixed:
        ze_exp.lang.as_fixed()

    result: Named = ze_exp.match("""abbbb""").result
    assert result.name == 'A'
    result = result.item[0]
    print(result)

    assert result.name == 'A'
    result = result.item[0]
    print(result)

    assert result.name == 'A'
    result = result.item[0]
    print(result)

    assert result.name == 'A'
    result = result.item[0]
    print(result)

    assert result.name == 'A'
    result = result.item
    assert isinstance(result, Tokenizer) and result.value == 'a'


def test_lr_indirect(fixed=False):
    ze_exp = ze.compile("""A ::= B 'a' | 'c'\nB ::= A 'b'""", use='A')
    if fixed:
        ze_exp.lang.as_fixed()

    result: Named = ze_exp.match("""cbaba""").result

    assert result.name == 'A'
    result = result.item[0]
    print(result)

    assert result.name == 'B'
    result = result.item[0]
    print(result)

    assert result.name == 'A'
    result = result.item[0]
    print(result)

    assert result.name == 'B'
    result = result.item[0]
    print(result)

    assert result.name == 'A'
    result = result.item
    assert isinstance(result, Tokenizer) and result.value == 'c'


def test_fixed():
    test_lr(True)
    test_lr_indirect(True)
