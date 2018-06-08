import rbnf.zero as zero

zero_exp = zero.compile("""
import std.common.[Number Name Space]
ignore [Space]
Numeric ::= Number as integer ['.' Number as floating]
            rewrite float(integer.value + '.' + floating.value) if floating else int(integer.value)
Term ::= [Numeric as coef] Name as root ['^' Number as power] | Numeric as coef
        with    not root or root.value == 'x'
        rewrite coef if coef else 1, int(power.value) if power else 1 if root else 0
Add ::= ('-' as neg | '+') Term as term
        rewrite
            coef, power = term
            -coef if neg else coef, power
Poly ::=  ['-' as neg] Term as head Add* as seq
        rewrite
            class Polynomial(dict):
                def __missing__(self, k):
                    return 0
            mapping = Polynomial()
            coef, power = head
            mapping[power] = -coef if neg else coef
            if any(seq):
                for coef, power in seq:
                    mapping[power] += coef
            sorted(mapping.items(), key=lambda kv: kv[0])""")
print(zero_exp("2x^2 + 3 + 4 - 7 x^5 + 4 x + 5 x ^2 - x + 7 x ^ 11").result)
