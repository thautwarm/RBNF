import rbnf.zero as ze
from Redy.Tools.PathLib import  Path
print(Path('./'))
zero_exp = ze.compile("""
import poly.[*]""", use='Poly')

print(zero_exp.match("2x^2 + 3 + 4 - 7 x^5 + 4 x + 5 x ^2 - x + 7 x ^ 11").result)
