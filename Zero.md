
# Zero

```python
import rbnf.zero as ze
ze_exp = ze.compile(rbnf_src_code)
print(ze_exp.match(text))
```

A vivid example with practical factors is presented [here](https://github.com/thautwarm/RBNF/blob/master/tests/zero_module.py), which aims to give out the coefs of any polynomials.

## Sample 1

```python

import rbnf.zero as ze
from pprint import pprint

ze_exp = ze.compile("""
[python] import rbnf.std.common.[recover_codes]
pattern := R'[^/\sa-z]+'
url ::= result = (('https:' | 'http:') '//' pattern+ ('/' pattern)* ['/'])
       -> result

text ::= (url to [urls]| ~url)+
        -> tuple(recover_codes(each) for each in urls)

pattern          := R'[a-zA-Z0-9_]+'
space            := R'\s+'
""", use='text')

from urllib.request import urlopen
text = urlopen('https://github.com/thautwarm/RBNF').read().decode()
pprint(ze_exp.match(text).result)

```

output: 
```
'https://assets-cdn.github.com">',
 'https://avatars0.githubusercontent.com">',
 'https://avatars1.githubusercontent.com">',
 'https://avatars2.githubusercontent.com">',
 'https://avatars3.githubusercontent.com">',
 'https://github-cloud.s3.amazonaws.com">',
 'https://user-images.githubusercontent.com/">',
 'https://assets-cdn.github.com/assets/frameworks',
 'https://assets-cdn.github.com/assets/github',
 'https://assets-cdn.github.com/assets/site',
 'https://github.com/thautwarm/R',
 'https://github.com/thautwarm/R',
 'https://github.com/fluidicon',
 'https://avatars1.githubusercontent.com/u/22536460?',
 'https://github.com/thautwarm/RBNF"',
 'https://github.com/thautwarm/R',
 'https://assets-cdn.github.com/">',
 'https://collector.githubapp.com/github',
 'https://github.com/thautwarm/RBNF/commits/master',
 'https://github.com/thautwarm/RBNF.',
 'https://github.com/thautwarm/RBNF"',
 'https://api.github.com/_',
 'https://api.github.com/_',
 'https://assets-cdn.github.com/pinned',
 'https://assets-cdn.github.com/favicon',
 'https://github.com/"',
 'https://assets-cdn.github.com/images/search',
 'https://assets-cdn.github.com/images/spinners/octocat',
 'http://schema.org/S',
 'http://schema.org/B',
 'http://schema.org/L',
 'http://schema.org/L',
 'http://schema.org/L',
 'https://github.com/thautwarm/R',
 'https://github.com/thautwarm/R',
 'https://help.github.com/articles/which',
 'https://github.com/thautwarm/RBNF.',
 'https://github.com/thautwarm/RBNF.',
 'https://github.com/thautwarm/RBNF.',
 'https://desktop.github.com/">',
 'https://desktop.github.com/">',
 'https://developer.apple.com/xcode/">',
 'https://visualstudio.github.com/">',
 'https://assets-cdn.github.com/images/spinners/octocat',
 'https://assets-cdn.github.com/images/spinners/octocat',
 'https://assets-cdn.github.com/images/spinners/octocat',
 'https://assets-cdn.github.com/images/spinners/octocat',
 'https://assets-cdn.github.com/images/spinners/octocat',
 'https://assets-cdn.github.com/images/spinners/octocat',
 'https://assets-cdn.github.com/images/spinners/octocat',
 'https://assets-cdn.github.com/images/spinners/octocat',
 'https://assets-cdn.github.com/images/spinners/octocat',
 'https://assets-cdn.github.com/images/spinners/octocat',
 'https://assets-cdn.github.com/images/spinners/octocat',
 'https://assets-cdn.github.com/images/spinners/octocat',
 'https://assets-cdn.github.com/images/spinners/octocat',
 'https://assets-cdn.github.com/images/spinners/octocat',
 'https://assets-cdn.github.com/images/spinners/octocat',
 'https://assets-cdn.github.com/images/spinners/octocat',
 'https://assets-cdn.github.com/images/spinners/octocat',
 'https://assets-cdn.github.com/images/spinners/octocat',
 'https://assets-cdn.github.com/images/spinners/octocat',
 'https://assets-cdn.github.com/images/spinners/octocat',
 'https://travis-ci.org/thautwarm/RBNF"',
 'https://camo.githubusercontent.com/41',
 'https://travis-ci.org/thautwarm/RBNF.',
 'https://pypi.python.org/pypi/rbnf',
 'https://camo.githubusercontent.com/52',
 'https://img.shields.io/pypi/v/RBNF.',
 'https://github.com/thautwarm/RBNF/blob/master/LICENSE"><',
 'https://camo.githubusercontent.com/25730',
 'https://img.shields.io/badge/license',
 'https://github.com/thautwarm/RBNF/blob/master/tutorials',
 'https://github.com/thautwarm/RBNF/blob/master/tests/poly',
 'https://github.com/thautwarm/reFining',
 'https://github.com/thautwarm/reFining',
 'https://github.com/thautwarm/rmalt',
 'https://github.com/thautwarm/rmalt',
 'https://github.com/thautwarm/RBNF/blob/master/rbnf/bootstrap/rbnf',
 'https://github.com/site/terms',
 'https://github.com/site/privacy',
 'https://help.github.com/articles/github',
 'https://status.github.com/"',
 'https://help.github.com">Help</a',
 'https://github.com">',
 'https://github.com/contact',
 'https://github.com/pricing',
 'https://developer.github.com"',
 'https://training.github.com"',
 'https://blog.github.com"',
 'https://github.com/about',
 'https://assets-cdn.github.com/assets/compat',
 'https://assets-cdn.github.com/assets/frameworks',
 'https://assets-cdn.github.com/assets/github')
```
