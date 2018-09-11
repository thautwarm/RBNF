from pprint import pprint
from prof_interactive import ze_exp as interactive
from urllib.request import urlopen

text = urlopen('https://github.com/thautwarm/RBNF').read().decode()

pprint(interactive.match(text).result)
