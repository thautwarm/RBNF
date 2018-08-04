import rbnf.zero as ze
import os
from rbnf.easy import build_parser
from Redy.Tools.PathLib import Path
os.chdir(Path(__file__).parent().__str__())
ze_exp = ze.compile('import simple_ml.[*]', use='Grammar')


def test_simple_ml():
    _test_simple_ml()
    ze_exp.lang.as_fixed()
    _test_simple_ml()

    parse = build_parser(ze_exp.lang, opt=True)
    print(parse("let x = 1 in x"))


def _test_simple_ml():

    print(
        repr(
            ze_exp.match("""
    let s = fn x: 'a -> x in
              let d = s "1" in
              let k = fn x: 'a -> x in 
              k;
    """).result))

    print(
        repr(
            ze_exp.match("""
    let x : 'a * int = (1, 2) in x 
    """).result))

    print(
        repr(
            ze_exp.match("""
        
    let x: 'a => 'b = fn x -> 1 in
    x * 2
        """).result))

    print(
        repr(
            ze_exp.match("""
    type F['a, 'b, 'c] = 'a * 'b * 'c
    """).result))

    print(
        repr(
            ze_exp.match("""
        (1, 2, 3, 4, (5, 6, 7))
        """).result))
    print(
        repr(
            ze_exp.match("""
        let f: 'a => ('b * c => d) = fn x -> x in f
        """).result))
