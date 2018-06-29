import rbnf.zero as ze
from visitor import visit
ze_exp = ze.compile('import calc.[*]', use='Add')


def loop():
    while True:
        inp = input('calc> ')
        if inp == 'exit':
            print('good bye!')
            break
        try:
            matched = ze_exp.match(inp)
            print('=> ', visit(matched.result))
        except Exception as e:
            print(repr(e))

loop()