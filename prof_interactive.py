import rbnf.zero as ze
import timeit

ze_exp = ze.compile("""
[python] import rbnf.std.common.[recover_codes]
pattern := R'[^/\sa-z]+'
url ::= (('https:' | 'http:') '//' pattern+ ('/' pattern)* ['/']) as result 
        -> result

text ::= (url to [urls]| ~url)+
            rewrite
              tuple(recover_codes(each) for each in urls)
              
pattern          := R'[a-zA-Z0-9_]+'
space            := R'\s+'
""", use='text')

with open('prof_compiled.py', 'w') as f:
    f.write(ze_exp.dumps())
    f.write('ulang.as_fixed()\n')
    f.write('_impl = ulang.implementation\n')
    f.write('from rbnf.core.State import State\n')
    f.write('_ze_exp = text.match\n')
    f.write('lexer = ulang.lexer\n')
    f.write('ze_exp = lambda text: _ze_exp(tuple(lexer(text)), State(_impl))')
