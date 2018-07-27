from pprint import pprint

import rbnf.zero as ze
from Redy.Tools.PathLib import Path

print(Path('./'))
zero_exp = ze.compile("""

# test
import poly.[*] # 1234""", use='Poly')

print(zero_exp.match("2x^2 + 3 + 4 - 7 x^5 + 4 x + 5 x ^2 - x + 7 x ^ 11").result)

lang = zero_exp._lang

"""

{'Add': (((('-') as neg | '+') (Term) as term),
         None,
         None,
         <function rewrite at 0x000002BED1A4A158>),
 'Numeric': (((N'Number') as integer (('.' (N'Number') as floating)){0 1}),
             None,
             None,
             <function rewrite at 0x000002BED1A31F28>),
 'Poly': (((('-') as neg){0 1} (Term) as head ((Add){0 -1}) as seq),
          None,
          None,
          <function rewrite at 0x000002BED1A4A268>),
 'Term': (((((Numeric) as coef){0 1} (N'Name') as root (('^' (N'Number') as power)){0 1}) | (Numeric) as coef),
          None,
          <function fail_if at 0x000002BED1A4A048>,
          <function rewrite at 0x000002BED1A4A0D0>)}
          
          
[('Name', N'Name'),
 ('Space', N'Space'),
 ('Number', N'Number'),
 ('Numeric', Numeric),
 ('Term', Term),
 ('Add', Add),
 ('Poly', Poly)]

"""
