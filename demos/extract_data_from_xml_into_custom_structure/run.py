import rbnf.zero as ze
from Redy.Tools.PathLib import Path

with Path("./task.rbnf").open('r') as f:
    ze_exp = ze.compile(f.read(), use='Test')


with open(Path("./data.xml").__str__(), encoding='utf8') as f:
    text = f.read()
    result = ze_exp.match(text).result

for each in result:
    print(each)


