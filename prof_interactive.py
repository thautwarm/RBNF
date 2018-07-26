import rbnf.zero as ze
import timeit

ze_exp = ze.compile("""
[python] import rbnf.std.common.[recover_codes Tokenizer]
import std.common.[Space]
pattern ::= (~ ('/' | Space))+ as seq
            rewrite 
                seq
url ::= ('https' | 'http') as prefix 
        '://'              as slash 
        pattern            as head 
        ('/' pattern)*     as tail 
        ['/'] 
        rewrite
            def stream():
                yield prefix
                yield slash
                yield from head
                yield from tail
            tuple(stream())
text ::= (url to [urls] | ~url)+
        rewrite
            tuple(recover_codes(each) for each in urls)
            
lexer_helper := R'.'
""", use='text')

# with open('prof_compiled.py', 'w') as f:
#     f.write(ze_exp.dumps())
#     f.write('_impl = ulang.implementation\n')
#     f.write('from rbnf.core.State import State\n')
#     f.write('_ze_exp = text.match\n')
#     f.write('lexer = ulang.lexer\n')
#     f.write('ze_exp = lambda text: _ze_exp(tuple(lexer(text)), State(_impl))')